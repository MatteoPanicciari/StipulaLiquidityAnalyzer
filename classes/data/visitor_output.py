from typing import Optional

from classes.data.abstract_computation import AbsComputation
from classes.data.visitor_entry import FunctionVisitorEntry, EventVisitorEntry
from classes.data.liquidity_expression import LiqExpr, LiqConst

# maximum number of times a function can appear in the same abstract computation (k-canonical)
K: int = 1

class VisitorOutput:
    def __init__(self):
        self.Q0 : str = ''  # initial state
        self.parties: list[str] = list()
        self.global_assets: list[str] = list()
        self.entries: set[FunctionVisitorEntry | EventVisitorEntry] = set() # set of all the clauses (Functions, Events) of the contract
        self.abs_computations: dict[FunctionVisitorEntry | EventVisitorEntry, set[AbsComputation]] = dict()
        self.final_states: list[str] = list()

        self.states: set[str] = set()
        self.Qq : dict[str, set[FunctionVisitorEntry | EventVisitorEntry]] = dict()
        self.Z : set[tuple[str, Optional[str]]] = set()

        self.abs_computations_to_final_state : set[AbsComputation] = set()
        self.functions_liq_type : dict[FunctionVisitorEntry | EventVisitorEntry, dict[str, dict[str, LiqExpr]]] = dict()
        self.abs_computations_liq_type : dict[AbsComputation, tuple[str, dict[str, LiqExpr]]] = dict()

        self.has_events: bool = False
        self.has_guards: bool = False

    def compute_results(self) -> bool:
        result = True

        print(f"\tFunction Liquidity Types:")
        for entry in self.entries:
            self.functions_liq_type[entry] = entry.get_env()
            print(f"\t\t{entry}")
            print(f"\t\t\t{self.functions_liq_type[entry]['start']} -> {self.functions_liq_type[entry]['end']}")
            print(f"\t\t\t{entry.asset_types}")

        print(f"\tAbstract Computations:")
        for fn in self.abs_computations:
            for abs_computation in self.abs_computations[fn]:
                self.abs_computations_to_final_state.add(abs_computation)
                print(f"\t\t{abs_computation}")
                print(f"\t\t\t{abs_computation.liq_type_begin[0]} -> {abs_computation.liq_type_end[-1]}")
                print(f"\t\t\t{abs_computation.asset_types}")
                for h in abs_computation.liq_type_end[-1]:
                    result = result and abs_computation.liq_type_end[-1][h] == LiqExpr(LiqConst.EMPTY)

        self.compute_qq()
        print("\tLiquidity Results:")
        print("\t\tEfficient Algorithm:")
        print(f"\t\t\tis {'' if self.efficient_algorithm() else 'NOT '}k-separate liquid")
        print(f"\t\t\tis {'' if self.efficient_algorithm_complete() else 'NOT '}liquid")
        if not self.abs_computations_to_final_state:
            return False

        return result

    # Definition 1 : constraint 1
    def compute_function_local_liquidity(self) -> tuple[bool, bool, bool]:
        for entry in self.entries:
            if type(entry).__name__ == FunctionVisitorEntry.__name__:
                p = entry.compute_local_liquidity()
                if p:
                    print(f"\t{entry}\n\t\tis NOT local liquid: {p}")
                    return False, self.has_events, self.has_guards
        return True, self.has_events, self.has_guards


    def set_init_state_id(self, state_id):
        self.Q0 = state_id

    def add_party(self, party_id):
        self.parties.append(party_id)

    def add_visitor_entry(self, visitor_entry: FunctionVisitorEntry | EventVisitorEntry, has_guard: bool = False):
        self.entries.add(visitor_entry)
        if type(visitor_entry).__name__ == EventVisitorEntry.__name__:
            self.has_events = True
        if has_guard:
            self.has_guards = True

    def add_global_asset(self, asset):
        self.global_assets.append(asset.text)

    def compute_r(self):
        # Base case
        # Initialize the dict foreach function
        # Value for 'f':
            # [f] if f starts from Q0
            # [] else
        for visitor_entry in self.entries:
            if isinstance(visitor_entry, FunctionVisitorEntry) and visitor_entry.start_state == self.Q0:
                self.abs_computations[visitor_entry] = { AbsComputation(visitor_entry) }
            else:
                self.abs_computations[visitor_entry] = set()

        is_change = True
        while is_change:
            is_change = False
            for current_entry in self.entries:
                set_tuples_to_add = set()
                for previous_entry in self.entries:
                    # checks if previous_entry goes to current_function start state
                    if previous_entry.end_state == current_entry.start_state:
                        for previous_fn_abs_computation in self.abs_computations[previous_entry]:
                            # foreach tuple in previous_entry.set:
                            #   checks if the current entry appears less than k times in the tuple
                            #   if True, add the entry to the tuple
                            new_previous_entry_tuple = previous_fn_abs_computation.copy_abs_computation()
                            if previous_fn_abs_computation.count(current_entry) < K:
                                new_previous_entry_tuple.insert_configuration(current_entry)
                            set_tuples_to_add.add(new_previous_entry_tuple)

                is_change = is_change or bool(set_tuples_to_add.difference(self.abs_computations[current_entry]))
                self.abs_computations[current_entry].update(set_tuples_to_add)

    def compute_qq(self):
        for state in self.states:
            self.Qq[state] = set()
        for entry in self.entries:
            self.Qq[entry.start_state].add(entry)
        is_change = True
        while is_change:
            is_change = False
            for entry in self.entries:
                before = len(self.Qq[entry.start_state])
                self.Qq[entry.start_state] |= self.Qq[entry.end_state]
                self.Qq[entry.start_state].add(entry)
                if len(self.Qq[entry.start_state]) > before:
                    is_change = True
    def compute_final_states(self):
        self.states = set()
        initial_states = set()
        for visitor_entry in self.entries:
            if type(visitor_entry).__name__ == FunctionVisitorEntry.__name__:
                self.states.add(visitor_entry.start_state)
                self.states.add(visitor_entry.end_state)
                initial_states.add(visitor_entry.start_state)
        self.final_states = self.states - initial_states


    def efficient_algorithm(self) -> bool:
        # step 1
        self.compute_qq()
        self.Z = set()

        found_missing_tuple = True
        while found_missing_tuple:
            found_missing_tuple = False
            # step 2
            for entry in self.Qq[self.Q0]:
                entry_env = entry.get_env()
                for k in self.global_assets:
                    # step 2.a, 2.b
                    if (entry_env['start'][k] != entry_env['end'][k] and
                        entry_env['end'][k] != LiqExpr(LiqConst.EMPTY) and
                        (entry.end_state, k) not in self.Z
                    ):
                        found_missing_tuple = True
                        is_missing_tuple_added = False
                        # step 2.2
                        for next_entry in self.Qq[entry.end_state]:
                            next_entry_env = next_entry.get_env()
                            if next_entry_env['end'][k] == LiqExpr(LiqConst.EMPTY):
                                is_missing_tuple_added = True
                                self.Z.add((entry.end_state, k))
                                break
                        if not is_missing_tuple_added:
                            print(f"\t\t\t\t{entry}, {k}")
                            return False
        # step 2.1
        return True

    def efficient_algorithm_complete(self) -> bool:
        # step 1
        self.Z = set()

        h = tuple()
        for k in self.global_assets:
            h += (k,)

        found_missing_tuple = True
        while found_missing_tuple:
            found_missing_tuple = False
            # step 2
            for entry in self.Qq[self.Q0]:
                entry_env = entry.get_env()

                h_not_zero = any(
                    entry_env['end'][k] != LiqExpr(LiqConst.EMPTY)
                    for k in self.global_assets
                )
                if h_not_zero and entry_env['start']!=entry_env['end'] and entry.end_state not in self.Z:
                    found_missing_tuple = True
                    is_missing_tuple_added = False
                    # step 2.2
                    for next_entry in self.Qq[entry.end_state]:
                        next_entry_env = next_entry.get_env()
                        all_zero = all(
                            next_entry_env['end'][k] == LiqExpr(LiqConst.EMPTY)
                            for k in self.global_assets
                        )
                        if all_zero:
                            is_missing_tuple_added = True
                            self.Z.add(entry.end_state)
                            break
                    if not is_missing_tuple_added:
                        print(f"\t\t\t\t{entry}")
                        return False
        # step 2.1
        return True
        self.final_states = states - initial_states
