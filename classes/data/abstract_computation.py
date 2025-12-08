from classes.data.visitor_entry import FunctionVisitorEntry
from classes.data.liquidity_expression import LiqExpr, LiqConst
from collections import Counter

class AbsComputation:
    def __init__(self, first_function: FunctionVisitorEntry = None):
        self.is_first_function_missing = True

        self.configurations : tuple[FunctionVisitorEntry] = tuple()
        self.liq_type : tuple[dict[str, LiqExpr]] = tuple()

        self.function_liq_type_begin : list[dict[str, LiqExpr]] = list()
        self.function_liq_type_end : list[dict[str, LiqExpr]] = list()

        if first_function:
            self.insert_function(first_function)

    def insert_function(self, function: FunctionVisitorEntry):
        self.configurations += (function,)
        #print('-------------------------')
        #print(function)

        # Compute: Liquidity type of abstract computation (Def 3)
        function_env = function.copy_function_type(only_global=True)    # TODO capire se qui vada effettivamente False
        #print(f"{function_env['start']} -> {function_env['end']}")
        if self.is_first_function_missing:
            self.is_first_function_missing = False
            self.function_liq_type_begin.append(function_env['start'])
            #print(f"begin = {self.function_liq_type_begin[-1]}")
        else:
            self.function_liq_type_begin.append(function_env['start'])
            for h in self.function_liq_type_begin[-1]:
                if h in function.global_assets and str(self.function_liq_type_begin[-1][h]) not in LiqConst.constants:
                    h_value = self.function_liq_type_end[-1][h].copy_liquidity()
                    self.function_liq_type_begin[-1][h].replace_value(str(self.function_liq_type_begin[-1][h]), h_value)
            #print(f"begin = {self.function_liq_type_begin[-1]}")

        self.function_liq_type_end.append(function_env['end'])
        for h in self.function_liq_type_end[-1]:
            if h in function.global_assets and str(self.function_liq_type_end[-1][h]) not in LiqConst.constants:
                h_value = self.function_liq_type_begin[-1][h].copy_liquidity()
                self.function_liq_type_end[-1][h].replace_value(str(self.function_liq_type_end[-1][h]), h_value)
        #print(f"end = {self.function_liq_type_end[-1]}")
        #print(f"{function_env['start']} -> {function_env['end']}")


    def count(self, function: FunctionVisitorEntry):
        return Counter(self.configurations)[function]

    def __str__(self):
        result = ''
        for configuration in self.configurations:
            result = f"{result}{configuration}; "
        return result
    __repr__ = __str__