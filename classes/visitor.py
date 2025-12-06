from generated.StipulaVisitor import StipulaVisitor
from generated.StipulaParser import StipulaParser

from classes.data.visitor_entry import FunctionVisitorEntry, CodeReference
from classes.data.liquidity_expression import LiqExpr, LiqConst
from classes.data.visitor_output import VisitorOutput

class Visitor(StipulaVisitor):
    def __init__(self):
        StipulaVisitor.__init__(self)
        self.visitor_output = VisitorOutput()

    def visitStipula(self, ctx: StipulaParser.StipulaContext):
        """
        Visit a parse tree produced by StipulaParser#stipula.
        Called by ANTLR visitor : StipulaParser.StipulaContext.accept()
        """
        if ctx.assetsDecl():
            self.visitAssetsDecl(ctx.assetsDecl())
        if ctx.agreement():
            self.visitAgreement(ctx.agreement())
        for function_decl_ctx in ctx.functionDecl():
            self.visitFunctionDecl(function_decl_ctx)

        self.visitor_output.compute_r()
        self.visitor_output.compute_final_states()
        self.visitor_output.compute_results(ctx.ID())

    def visitAssetsDecl(self, ctx:StipulaParser.AssetsDeclContext):
        """
        Visit assets declaration
        i.e. : assets h1, h2
        """
        for a in ctx.assetId:
            self.visitor_output.add_global_asset(a)

    def visitAgreement(self, ctx:StipulaParser.AgreementContext):
        """
        Visit agreement
        i.e. : agreement(parts) { f } => @Q0
        """
        self.visitor_output.set_init_state_id(ctx.stateId.text) # set Q0 on visitor_output
        for party in ctx.ID():
            self.visitor_output.add_party(party.getText())

    def visitFunctionDecl(self, ctx:StipulaParser.FunctionDeclContext):
        """
        Visit function declaration
        i.e. FunctionVisitorEntry call : (start_state=Q0, handler=Alice, code_id=fill, end_state=Q1, code_reference=(9, 11))
        """
        list_of_xi = [a for a in self.visitor_output.global_assets]
        list_of_ones = [a.text for a in ctx.assetId]
        function_visitor_entry = FunctionVisitorEntry(ctx.startStateId.text, ctx.partyId.text, ctx.functionId.text, ctx.endStateId.text, CodeReference(ctx.start.line, ctx.stop.line), list_of_xi, list_of_ones)
        self.visitor_output.add_visitor_entry(function_visitor_entry)   # update C and Lc on visitor_output

        # visit function body
        for func_statement_ctx in ctx.functionBody().statement():
            if func_statement_ctx.ifThenElse():
                self.visitIfThenElse(func_statement_ctx.ifThenElse(), function_visitor_entry)
            elif func_statement_ctx.assetOperation():
                self.visitAssetOperation(func_statement_ctx.assetOperation(), function_visitor_entry)
            elif func_statement_ctx.fieldOperation():
                self.visitFieldOperation(func_statement_ctx.fieldOperation())
            else:
                print("ERROR visitFunctionDecl")

    def visitIfThenElse(self, ctx: StipulaParser.IfThenElseContext, function_visitor_entry: FunctionVisitorEntry = None) -> dict[str, LiqExpr]:
        if ctx.expression():
            if self.visitExpression(ctx.expression()) != 'BOOL':
                # TODO capire se puo assumere anche altri valori
                print("ERROR visitIfThenElse")
                return {}

            if ctx.functionBody(0):
                then_environment = self.visitFunctionBody(ctx.functionBody(0), function_visitor_entry)
                if ctx.functionBody(1):
                    else_environment = self.visitFunctionBody(ctx.functionBody(1), function_visitor_entry)
                elif ctx.ifThenElse():
                    else_environment = self.visitIfThenElse(ctx.ifThenElse(), function_visitor_entry)
                else:
                    print("ERROR visitIfThenElse")
                    return {}

                for el in function_visitor_entry.function_type_output:
                    function_visitor_entry.set_field_value(el, LiqExpr(LiqConst.upper_operator, then_environment[el], else_environment[el]))
                return function_visitor_entry.get_function_type()['out']

        print("ERROR visitIfThenElse")
        return {}

    def visitFunctionBody(self, ctx: StipulaParser.FunctionBodyContext, function_visitor_entry: FunctionVisitorEntry = None) -> dict[str, LiqExpr]:
        function_visitor_entry.add_function_level()
        for func_statement_ctx in ctx.statement():
            if func_statement_ctx.ifThenElse():
                self.visitIfThenElse(func_statement_ctx.ifThenElse(), function_visitor_entry)
            elif func_statement_ctx.assetOperation():
                self.visitAssetOperation(func_statement_ctx.assetOperation(), function_visitor_entry)
            elif func_statement_ctx.fieldOperation():
                self.visitFieldOperation(func_statement_ctx.fieldOperation())
            else:
                print("ERROR visitFunctionDecl")
        result = function_visitor_entry.get_function_type()['out']
        function_visitor_entry.del_function_level()
        return result

    def visitAssetOperation(self, ctx: StipulaParser.AssetOperationContext, function_visitor_entry: FunctionVisitorEntry = None):
        if ctx.expression():
            left_type = self.visitExpression(ctx.expression())
            if ctx.ID(1):
                # left -o right,destination
                destination_id = ctx.ID(1).getText()
                if left_type == 'ID':
                    # left is an asset
                    left_id = ctx.expression().getText()
                    if destination_id not in self.visitor_output.parties:
                        # [L-EXPAUND]
                        destination_value = function_visitor_entry.get_current_field_value(destination_id)
                        left_value = function_visitor_entry.get_current_field_value(left_id)
                        destination_value.add_operation(LiqConst.upper_operator, left_value)
                pass
            else:
                # left -o destination
                destination_id = ctx.ID(0).getText()
                if left_type == 'ID':
                    # left is an asset
                    left_id = ctx.expression().getText()

                    if destination_id not in self.visitor_output.parties:
                        # [L-AUPDATE]
                        destination_value = function_visitor_entry.get_current_field_value(destination_id)
                        left_value = function_visitor_entry.get_current_field_value(left_id)
                        destination_value.add_operation(LiqConst.upper_operator, left_value)
                    # [L-AUPDATE] [L-ASEND]
                    function_visitor_entry.set_field_value(left_id, LiqExpr(LiqConst.empty))
                else:
                    # left is a value
                    # TODO ?
                    pass

    def visitFieldOperation(self, ctx: StipulaParser.FieldOperationContext):
        print(f"fieldOperation {ctx.getText()}")

    def visitExpression(self, ctx: StipulaParser.ExpressionContext) -> str:
        if ctx.expression1():
            left_exp_type = self.visitExpression1(ctx.expression1())
            if ctx.expression():
                if left_exp_type and self.visitExpression(ctx.expression()):
                    return 'BOOL'
                return ''
            return left_exp_type
        return ''

    def visitExpression1(self, ctx: StipulaParser.Expression1Context) -> str:
        #print(f"expression1 {ctx.getText()}")
        if ctx.expression2():
            left_exp_type = self.visitExpression2(ctx.expression2())
            if ctx.NOT():
                if left_exp_type == 'BOOL':
                    return 'BOOL'
                return ''
            return left_exp_type
        return ''

    def visitExpression2(self, ctx: StipulaParser.Expression2Context) -> str:
        #print(f"expression2 {ctx.getText()}")
        if ctx.expression3():
            left_exp_type = self.visitExpression3(ctx.expression3())
            if ctx.expression2():
                if left_exp_type and self.visitExpression2(ctx.expression2()):
                    return 'BOOL'
                return ''
            return left_exp_type
        return ''

    def visitExpression3(self, ctx: StipulaParser.Expression3Context) -> str:
        #print(f"expression3 {ctx.getText()}")
        if ctx.expression4():
            left_exp_type = self.visitExpression4(ctx.expression4())
            if ctx.expression3():
                right_exp_type = self.visitExpression3(ctx.expression3())
                # TODO controllo del tipo? se STRING, non posso fare il TIMES
                if left_exp_type == right_exp_type:
                    return left_exp_type
                return ''
            return left_exp_type
        return ''


    def visitExpression4(self, ctx: StipulaParser.Expression4Context) -> str:
        #print(f"expression4 {ctx.getText()}")
        if ctx.expression5():
            left_exp_type = self.visitExpression5(ctx.expression5())
            if ctx.expression4():
                right_exp_type = self.visitExpression4(ctx.expression4())
                # TODO controllo del tipo? se STRING, non posso fare il TIMES
                if left_exp_type == right_exp_type:
                    return left_exp_type
                return ''
            return left_exp_type
        return ''

    def visitExpression5(self, ctx: StipulaParser.Expression5Context) -> str:
        #print(f"expression5 {ctx.getText()}")
        if ctx.expression6():
            # TODO controllo del tipo? se STRING, non posso metterci il MINUS
            return self.visitExpression6(ctx.expression6())
        return ''

    def visitExpression6(self, ctx: StipulaParser.Expression6Context) -> str:
        #print(f"expression6 {ctx.getText()}")
        if ctx.NOW():
            return 'NOW'
        elif ctx.BOOL():
            return 'BOOL'
        elif ctx.TIMEDELTA():
            return 'TIMEDELTA'
        elif ctx.NUMBER():
            return 'NUMBER'
        elif ctx.DATESTRING():
            return 'DATESTRING'
        elif ctx.STRING():
            return 'STRING'
        elif ctx.ID():
            return 'ID'
        elif ctx.expression():
            return self.visitExpression(ctx.expression())
        else:
            return ''   # ERROR