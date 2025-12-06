from classes.data.visitor_entry import FunctionVisitorEntry
from classes.data.liquidity_expression import LiqExpr
from collections import Counter

class AbsComputation:
    xi_count : int = 1

    def __init__(self, first_function: FunctionVisitorEntry = None):

        self.configurations : tuple[FunctionVisitorEntry] = tuple()
        self.liq_type : tuple[dict[str, LiqExpr]] = tuple()

        if first_function:
            self.insert_function(first_function)

    def insert_function(self, function: FunctionVisitorEntry):
        self.configurations += (function,)

    def count(self, function: FunctionVisitorEntry):
        return Counter(self.configurations)[function]

    def __str__(self):
        result = ''
        for configuration in self.configurations:
            result = f"{result}{configuration}; "
        return result
    __repr__ = __str__