from __future__ import annotations
from classes.data.visitor_entry import FunctionVisitorEntry, EventVisitorEntry
from classes.data.liquidity_expression import LiqExpr, LiqConst
from collections import Counter

class AbsComputation:
    def __init__(self, first_function: FunctionVisitorEntry | EventVisitorEntry = None):
        self.is_first_function_missing = True

        self.configurations : tuple[FunctionVisitorEntry | EventVisitorEntry] = tuple()
        self.liq_type : tuple[dict[str, LiqExpr]] = tuple()

        self.liq_type_begin : list[dict[str, LiqExpr]] = list()
        self.liq_type_end : list[dict[str, LiqExpr]] = list()

        if first_function:
            self.insert_configuration(first_function)

    def insert_configuration(self, entry: FunctionVisitorEntry | EventVisitorEntry):
        self.configurations += (entry,)

        # Compute: Liquidity type of abstract computation (Def 3)
        entry_env = entry.copy_env()
        if self.is_first_function_missing:
            self.is_first_function_missing = False
            self.liq_type_begin.append(entry_env['start'])
            if True:    # TODO capire se gli assets vanno inizializzati effettivamente a 0
                for h in self.liq_type_begin[-1]:
                    self.liq_type_begin[-1][h].replace_value(str(self.liq_type_begin[-1][h]), LiqExpr(LiqConst.EMPTY))
        else:
            self.liq_type_begin.append(entry_env['start'])
            for h in self.liq_type_begin[-1]:
                if h in entry.global_assets and str(self.liq_type_begin[-1][h]) not in LiqConst.CONSTANTS:
                    h_value = self.liq_type_end[-1][h].copy_liquidity()
                    self.liq_type_begin[-1][h].replace_value(str(self.liq_type_begin[-1][h]), h_value)
                    self.liq_type_begin[-1][h] = LiqExpr.resolve_partial_eval(self.liq_type_begin[-1][h])

        self.liq_type_end.append(entry_env['end'])
        for h in self.liq_type_end[-1]:
            if h in entry.global_assets and str(self.liq_type_end[-1][h]) not in LiqConst.CONSTANTS:
                h_value = self.liq_type_begin[-1][h].copy_liquidity()
                self.liq_type_end[-1][h].replace_value(str(self.liq_type_end[-1][h]), h_value)
                self.liq_type_end[-1][h] = LiqExpr.resolve_partial_eval(self.liq_type_end[-1][h])

    def count(self, entry: FunctionVisitorEntry | EventVisitorEntry):
        return Counter(self.configurations)[entry]

    def __str__(self):
        result = ''
        for configuration in self.configurations:
            result = f"{result}{configuration}; "
        return result
    __repr__ = __str__

    def copy_abs_computation(self) -> AbsComputation:
        result = AbsComputation()
        for configuration in self.configurations:
            result.insert_configuration(configuration)
        self.is_first_function_missing = len(self.configurations) == 0

        return result

    def __eq__(self, other):
        if isinstance(other, AbsComputation):
            return self.configurations == other.configurations
        return False

    # used when an AbsComputation obj is added into a structure like a set
    # called by set.difference()
    def __hash__(self):
        def dict_to_tuple(d):
            return tuple(sorted((k, str(v)) for k, v in d.items()))

        return hash((
            self.configurations,
            tuple(dict_to_tuple(d) for d in self.liq_type_begin),
            tuple(dict_to_tuple(d) for d in self.liq_type_end),
        ))
