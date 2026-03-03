from __future__ import annotations
from collections import Counter

from classes.data.visitor_entry import FunctionVisitorEntry, EventVisitorEntry
from classes.data.liquidity_expression import LiqExpr

class AbsComputation:
    def __init__(self):
        self.is_first_function_missing = True

        # list of entry in the computation
        self.configurations : tuple[FunctionVisitorEntry | EventVisitorEntry] = tuple()

        # liquidity type of the abstract computation
        self.liq_type_begin : list[dict[str, LiqExpr]] = list()
        self.liq_type_end : list[dict[str, LiqExpr]] = list()

        # events table - list of callable events for this abs_comp
        self.available_events : list[EventVisitorEntry] = list()

    def compute_liquidity_type(self, result, prev, entry_env_idx: str):
        entry = self.configurations[-1]
        entry_env = entry.get_env()
        for idx in entry.get_global_assets():
            result[idx] = entry_env[entry_env_idx][idx].copy_liquidity()
        for idx in entry.get_global_assets():
            for prev_idx in entry.get_global_assets():
                result[idx].replace_value(str(entry_env['start'][prev_idx]), prev[prev_idx].copy_liquidity())
                result[idx] = LiqExpr.resolve_partial_eval(result[idx])

    def insert_configuration(self, entry: FunctionVisitorEntry | EventVisitorEntry) -> None:
        """
            Insert a liquidity entry at the end of the abs_computation

        :param entry: function or event to add
        """
        self.configurations += (entry,)

        # Compute: Liquidity type of abstract computation (Def 3)
        # Def 3 - begin
        self.liq_type_begin.append(dict())
        if self.is_first_function_missing:
            self.is_first_function_missing = False
            for h in entry.global_assets:
                self.liq_type_begin[-1][h] = entry.get_env()['start'][h].copy_liquidity()
        else:
            self.compute_liquidity_type(self.liq_type_begin[-1], self.liq_type_end[-1], 'start')

        # Def 3 - end
        self.liq_type_end.append(dict())
        self.compute_liquidity_type(self.liq_type_end[-1], self.liq_type_begin[-1], 'end')


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

    def get_available_events(self) -> list[EventVisitorEntry]:
        return self.available_events

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
        #  dalla seconda volta che son passato in quello stato, riceverò sempre la prima ig
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