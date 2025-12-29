from __future__ import annotations
import itertools
from collections import Counter

from classes.data.asset_types import AssetTypes
from classes.data.visitor_entry import FunctionVisitorEntry, EventVisitorEntry
from classes.data.liquidity_expression import LiqExpr, LiqConst

class AbsComputation:
    def __init__(self):
        self.is_first_function_missing = True

        # list of entry in the computation
        self.configurations : tuple[FunctionVisitorEntry | EventVisitorEntry] = tuple()

        # liquidity type of the abstract computation
        self.liq_type_begin : list[dict[str, LiqExpr]] = list()
        self.liq_type_end : list[dict[str, LiqExpr]] = list()

        self.asset_types : AssetTypes = AssetTypes()

        # True if asset_types is composed only by singletons
        self.are_all_types_singleton = True

        # events table - list of callable events for this abs_comp
        self.available_events : list[EventVisitorEntry] = list()


    def insert_configuration(self, entry: FunctionVisitorEntry | EventVisitorEntry) -> None:
        """
            Insert a liquidity entry at the end of the abs_computation

        :param entry: function or event to add
        """
        self.configurations += (entry,)

        # Compute: Liquidity type of abstract computation (Def 3)
        # Def 3 - begin
        entry_env = entry.copy_global_env()
        if self.is_first_function_missing:
            self.is_first_function_missing = False
            self.liq_type_begin.append(entry_env['start'])
            for h in self.liq_type_begin[-1]:
                self.liq_type_begin[-1][h].replace_value(str(self.liq_type_begin[-1][h]), LiqExpr(LiqConst.EMPTY))
                self.asset_types.add_singleton(h)
        else:
            self.liq_type_begin.append(entry_env['start'])
            for h in self.liq_type_begin[-1]:
                if h in entry.get_global_assets() and str(self.liq_type_begin[-1][h]) not in LiqConst.CONSTANTS:
                    h_value = self.liq_type_end[-1][h].copy_liquidity()
                    self.liq_type_begin[-1][h].replace_value(str(self.liq_type_begin[-1][h]), h_value)
                    self.liq_type_begin[-1][h] = LiqExpr.resolve_partial_eval(self.liq_type_begin[-1][h])
        # Def 3 - end
        self.liq_type_end.append(entry_env['end'])
        for h in self.liq_type_end[-1]:
            if h in entry.get_global_assets() and str(self.liq_type_end[-1][h]) not in LiqConst.CONSTANTS:
                h_value = self.liq_type_begin[-1][h].copy_liquidity()
                self.liq_type_end[-1][h].replace_value(str(self.liq_type_end[-1][h]), h_value)
                self.liq_type_end[-1][h] = LiqExpr.resolve_partial_eval(self.liq_type_end[-1][h])

        # Merges the abs_computation asset_types according to the asset_types sets contained in the entry.
        # If the asset types A and B are merged in the entry, the groups already formed in abs_computation
        # that contain A and B will also be merged.
        for g in entry.get_asset_types():
            for (a,b) in itertools.combinations(g, 2):
                if a in entry.get_global_assets() and b in entry.get_global_assets():
                    self.asset_types.merge_types(a,b)
                    self.are_all_types_singleton = False


    def count(self, entry: FunctionVisitorEntry | EventVisitorEntry) -> int:
        """
        :param entry: entry to count
        :return: number of times entry appears in the computation
        """
        return Counter(self.configurations)[entry]

    # region getter, setter
    def get_last_state(self) -> str:
        if self.configurations:
            return self.configurations[-1].get_end_state()
        return ''

    def get_asset_types(self) -> AssetTypes:
        return self.asset_types

    def get_available_events(self) -> list[EventVisitorEntry]:
        return self.available_events

    def get_are_all_types_singleton(self) -> bool:
        return self.are_all_types_singleton

    def get_env(self) -> dict[str, dict[str,LiqExpr]]:
        return {'start': self.liq_type_begin[0], 'end': self.liq_type_end[-1]}

    def add_available_event(self, event):
        self.available_events.append(event)

    def remove_available_event(self, event):
        if event in self.available_events:
            self.available_events.remove(event)
    # endregion getter, setter

    # region magic methods, deep_copy
    def __str__(self):
        result = ''
        for configuration in self.configurations:
            result = f"{result}{configuration}; "
        return result
    __repr__ = __str__

    def copy_abs_computation(self, initial_state: str = '') -> AbsComputation:
        # TODO: possibile problema con comp in cui passo piu volte nello stesso stato, se voglio copiare la comp
        #  dalla seconda volta che son passato in quello ststo, ricverò sempre la prima ig
        """
        :param initial_state: The computation copied will start from the initial_state (if it occurs in the computation).
            If empty, the copied computation will be exactly the same
        :return: deep-copy of the abs_computation
        """
        result = AbsComputation()
        if initial_state:
            append = False
            for configuration in self.configurations:
                if configuration.get_start_state() == initial_state:
                    append = True
                if append:
                    result.insert_configuration(configuration)
        else:
            for configuration in self.configurations:
                result.insert_configuration(configuration)
            self.is_first_function_missing = len(self.configurations) == 0
        result.available_events = list(self.available_events)
        return result

    def __eq__(self, other):
        if isinstance(other, AbsComputation):
            # return self.configurations == other.configurations and self.available_events == other.available_events
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

    def __iter__(self):
        return iter(self.configurations)
    # endregion magic methods, deep_copy