from classes.data.liquidity_expression import LiqExpr, LiqConst

class CodeReference:
    def __init__(self, start_line, end_line):
        self.start_line = start_line
        self.end_line = end_line

class VisitorEntry:
    def __init__(self, start_state, handler, code_id, end_state, code_reference: CodeReference):
        self.start_state = start_state
        self.handler = handler
        self.code_id = code_id
        self.end_state = end_state
        self.code_reference = code_reference

class FunctionVisitorEntry(VisitorEntry):
    xi_count : int = 1
    def __init__(self, start_state, handler, code_id, end_state, code_reference, global_assets, local_assets):
        super().__init__(start_state, handler, code_id, end_state, code_reference)

        self.function_type_input: dict[str, LiqExpr] = {}
        self.function_type_output: dict[str, list[LiqExpr | None]] = {}
        self.global_assets = global_assets
        self.local_assets = local_assets

        for h in global_assets:
            self.function_type_input[h] = LiqExpr(f'{LiqConst.XI}{self.xi_count}')
            self.function_type_output[h] = [LiqExpr(f'{LiqConst.XI}{self.xi_count}')]
            self.xi_count += 1

        for p in local_assets:
            self.function_type_input[p] = LiqExpr(LiqConst.FULL)
            self.function_type_output[p] = [LiqExpr(LiqConst.FULL)]

    def add_function_level(self):
        for el in self.function_type_output:
            self.function_type_output[el].append(None)

    def del_function_level(self):
        for el in self.function_type_output:
            self.function_type_output[el].pop()

    def set_field_value(self, field: str, value: LiqExpr):
        self.function_type_output[field][-1] = value

    def get_current_field_value(self, field) -> LiqExpr:
        count = 1
        res = None
        while not res and count <= len(self.function_type_output[field]):
            res = self.function_type_output[field][-count]
            count+=1
        return res

    def get_function_type(self) -> dict[str, dict[str,LiqExpr]]:
        function_type_output_result = {}
        for el in self.function_type_output:
            function_type_output_result[el] = LiqExpr.resolve_partial_eval(self.get_current_field_value(el))
        return {'start': self.function_type_input, 'end': function_type_output_result}

    def copy_function_type(self, only_global: bool = False) -> dict[str, dict[str,LiqExpr]]:
        function_type = self.get_function_type()
        function_type_result = dict(start=dict(), end=dict())
        for el in self.global_assets:
            function_type_result['start'][el] = function_type['start'][el].copy_liquidity()
            function_type_result['end'][el] = function_type['end'][el].copy_liquidity()
        if not only_global:
            for el in self.local_assets:
                function_type_result['start'][el] = function_type['start'][el].copy_liquidity()
                function_type_result['end'][el] = function_type['end'][el].copy_liquidity()
        return function_type_result


    def __str__(self):
        return f"{self.start_state} {self.handler}:{self.code_id} {self.end_state}"
    __repr__ = __str__