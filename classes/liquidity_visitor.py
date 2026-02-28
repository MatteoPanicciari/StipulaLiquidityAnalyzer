from generated.StipulaVisitor import StipulaVisitor
from generated.StipulaParser import StipulaParser

from classes.data.visitor_entry import FunctionVisitorEntry, EventVisitorEntry
from classes.data.liquidity_expression import LiqExpr, LiqConst
from classes.liquidity_analyzer import LiquidityAnalyzer

class LiquidityVisitor(StipulaVisitor):
    def __init__(self, function_frequency, is_verbose):
        StipulaVisitor.__init__(self)
        self.is_verbose = is_verbose
        self.analyzer = LiquidityAnalyzer(function_frequency)

        self.parties : list[str] = list()

    def compute_results(self, contract_name: str):
        print("___________________________________________"
              "\n|=========================================|"
              "\n¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯"
              f"\n{contract_name}")
        result_liquidity = self.analyzer.compute_results_verbose() if self.is_verbose else self.analyzer.compute_results()
        print(f"\n{contract_name} is{'' if result_liquidity[0] else ' NOT'} liquid")
        print(f"has events: {result_liquidity[1]}")
        print(f"has guards: {result_liquidity[2]}")

    def visitStipula(self, ctx: StipulaParser.StipulaContext):
        """
        Visit a parse tree produced by StipulaParser#stipula.
        Called by ANTLR visitor : StipulaParser.StipulaContext.accept()
        """
        if ctx.assetsDecl():
            self.visitAssetsDecl(ctx.assetsDecl())
        if ctx.fieldsDecl():
            self.visitFieldsDecl(ctx.fieldsDecl())
        if ctx.agreement():
            self.visitAgreement(ctx.agreement())
        for function_decl_ctx in ctx.functionDecl():
            self.visitFunctionDecl(function_decl_ctx)

        self.compute_results(ctx.ID())

    def visitAssetsDecl(self, ctx:StipulaParser.AssetsDeclContext):
        """
        Visit assets declaration
        i.e. : assets h1, h2
        """
        for a in ctx.assetId:
            self.analyzer.add_global_asset(a)

    def visitFieldsDecl(self, ctx:StipulaParser.FieldsDeclContext):
        """
        Visit fields declaration
        i.e. : fields x1, x2
        """
        pass

    def visitAgreement(self, ctx:StipulaParser.AgreementContext):
        """
        Visit agreement
        i.e. : agreement(parts) { f } => @Q0
        """
        self.analyzer.set_q0(ctx.stateId.text) # set Q0 on visitor_output
        for party in ctx.ID():
            self.parties.append(party.getText())

    def visitFunctionDecl(self, ctx:StipulaParser.FunctionDeclContext):
        """
        Visit function declaration
        i.e. : @Q0 A.f (x)[k](e==e1) { k -o A } => Q1
        """
        list_of_local_assets = {a.text for a in ctx.assetId}
        has_guard = bool(ctx.precondition)
        function_visitor_entry = FunctionVisitorEntry(ctx.startStateId.text, ctx.partyId.text,
                                                      ctx.functionId.text, ctx.endStateId.text,
                                                      self.analyzer.get_global_asset(), list_of_local_assets, has_guard)
        self.analyzer.add_visitor_function(function_visitor_entry, has_guard)   # update C and Lc on visitor_output

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
        for func_event_ctx in ctx.functionBody().eventDecl():
            function_visitor_entry.add_event(self.visitEventDecl(func_event_ctx))

    def visitEventDecl(self, ctx:StipulaParser.EventDeclContext) -> EventVisitorEntry:
        """
        Visit event declaration
        i.e. : now >> @Q0 { h -o A } => @Q1
        """
        event_visitor_entry = EventVisitorEntry(ctx.trigger.getText(), ctx.startStateId.text, ctx.endStateId.text, self.analyzer.get_global_asset())
        self.analyzer.add_visitor_event(event_visitor_entry)
        for func_statement_ctx in ctx.statement():
            if func_statement_ctx.ifThenElse():
                self.visitIfThenElse(func_statement_ctx.ifThenElse(), event_visitor_entry)
            elif func_statement_ctx.assetOperation():
                self.visitAssetOperation(func_statement_ctx.assetOperation(), event_visitor_entry)
            elif func_statement_ctx.fieldOperation():
                self.visitFieldOperation(func_statement_ctx.fieldOperation())
            else:
                print("ERROR visitEventDecl")
        return event_visitor_entry

    def visitIfThenElse(self, ctx: StipulaParser.IfThenElseContext, visitor_entry: FunctionVisitorEntry | EventVisitorEntry = None) -> dict[str, LiqExpr]:
        if ctx.expression():
            if ctx.functionBody(0):
                then_environment = self.visitFunctionBody(ctx.functionBody(0), visitor_entry)
                if ctx.functionBody(1):
                    else_environment = self.visitFunctionBody(ctx.functionBody(1), visitor_entry)
                elif ctx.ifThenElse():
                    else_environment = self.visitIfThenElse(ctx.ifThenElse(), visitor_entry)
                else:
                    print("ERROR visitIfThenElse")
                    return {}

                for el in visitor_entry.get_output_type():
                    visitor_entry.set_field_value(el, LiqExpr(LiqConst.UPPER, then_environment[el], else_environment[el]))
                return visitor_entry.get_env()['end']

        print("ERROR visitIfThenElse")
        return {}

    def visitFunctionBody(self, ctx: StipulaParser.FunctionBodyContext, visitor_entry: FunctionVisitorEntry | EventVisitorEntry = None) -> dict[str, LiqExpr]:
        visitor_entry.add_env_level()
        for func_statement_ctx in ctx.statement():
            if func_statement_ctx.ifThenElse():
                self.visitIfThenElse(func_statement_ctx.ifThenElse(), visitor_entry)
            elif func_statement_ctx.assetOperation():
                self.visitAssetOperation(func_statement_ctx.assetOperation(), visitor_entry)
            elif func_statement_ctx.fieldOperation():
                self.visitFieldOperation(func_statement_ctx.fieldOperation())
            else:
                print("ERROR visitFunctionDecl")
        result = visitor_entry.get_env()['end']
        visitor_entry.del_env_level()
        return result

    def visitAssetOperation(self, ctx: StipulaParser.AssetOperationContext, visitor_entry: FunctionVisitorEntry | EventVisitorEntry = None):
        if ctx.expression():
            left_type = self.visitExpression(ctx.expression())
            if ctx.ID(1):
                # left -o right,destination
                right_id = ctx.ID(0).getText()
                destination_id = ctx.ID(1).getText()
                if left_type == 'ID':
                    # left is an asset
                    left_id = ctx.expression().getText()
                    if destination_id not in self.parties:
                        # [L-EXPAUND]
                        destination_value = visitor_entry.get_current_field_value(destination_id)
                        left_value = visitor_entry.get_current_field_value(left_id)
                        destination_value.add_operation(LiqConst.UPPER, left_value)
                        visitor_entry.merge_function_asset_types(left_id, right_id)
            else:
                # left -o destination
                destination_id = ctx.ID(0).getText()
                if left_type == 'ID':
                    # left is an asset
                    left_id = ctx.expression().getText()

                    if destination_id not in self.parties:
                        # [L-AUPDATE]
                        destination_value = visitor_entry.get_current_field_value(destination_id)
                        left_value = visitor_entry.get_current_field_value(left_id)
                        destination_value.add_operation(LiqConst.UPPER, left_value)
                    # [L-AUPDATE] [L-ASEND]
                    visitor_entry.set_field_value(left_id, LiqExpr(LiqConst.EMPTY))
                    if destination_id not in self.parties:
                        visitor_entry.merge_function_asset_types(left_id, destination_id)
                else:
                    # left is a value
                    pass

    def visitFieldOperation(self, ctx: StipulaParser.FieldOperationContext):
        pass

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
        if ctx.expression2():
            left_exp_type = self.visitExpression2(ctx.expression2())
            if ctx.NOT():
                if left_exp_type == 'BOOL':
                    return 'BOOL'
                return ''
            return left_exp_type
        return ''

    def visitExpression2(self, ctx: StipulaParser.Expression2Context) -> str:
        if ctx.expression3():
            left_exp_type = self.visitExpression3(ctx.expression3())
            if ctx.expression2():
                if left_exp_type and self.visitExpression2(ctx.expression2()):
                    return 'BOOL'
                return ''
            return left_exp_type
        return ''

    def visitExpression3(self, ctx: StipulaParser.Expression3Context) -> str:
        if ctx.expression4():
            left_exp_type = self.visitExpression4(ctx.expression4())
            if ctx.expression3():
                right_exp_type = self.visitExpression3(ctx.expression3())
                if left_exp_type == right_exp_type:
                    return left_exp_type
                elif left_exp_type == 'NUMBER':
                    return right_exp_type
                elif right_exp_type == 'NUMBER':
                    return left_exp_type
                return ''
            return left_exp_type
        return ''


    def visitExpression4(self, ctx: StipulaParser.Expression4Context) -> str:
        if ctx.expression5():
            left_exp_type = self.visitExpression5(ctx.expression5())
            if ctx.expression4():
                right_exp_type = self.visitExpression4(ctx.expression4())
                if left_exp_type == right_exp_type:
                    return left_exp_type
                elif left_exp_type == 'NUMBER':
                    return right_exp_type
                elif right_exp_type == 'NUMBER':
                    return left_exp_type
                return ''
            return left_exp_type
        return ''

    def visitExpression5(self, ctx: StipulaParser.Expression5Context) -> str:
        if ctx.expression6():
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