from classes.data.abstract_computation import AbsComputation
from classes.data.visitor_entry import FunctionVisitorEntry, EventVisitorEntry
from classes.data.liquidity_expression import LiqExpr, LiqConst

# maximum number of times a function can appear in the same abstract computation (k-canonical)
K: int = 1

class VisitorOutput:
    def __init__(self):
        self.Q0 : str = ''  # initial state
        self.parties: list[str] = list()
        self.global_assets: set[str] = set()
        self.functions: set[FunctionVisitorEntry] = set()
        self.events: set[EventVisitorEntry] = set()
        self.abs_computations: set[AbsComputation] = set()
        self.final_states: set[str] = set()
        self.reachable_states: set[str] = set()

        self.states: set[str] = set()
        self.Tqk : dict[str, set[AbsComputation]] = dict()
        self.Qq : dict[str, set[FunctionVisitorEntry | EventVisitorEntry]] = dict()

        self.abs_computations_to_final_state : set[AbsComputation] = set()
        self.functions_liq_type : dict[FunctionVisitorEntry | EventVisitorEntry, dict[str, dict[str, LiqExpr]]] = dict()

        self.has_events: bool = False
        self.has_guards: bool = False


    def compute_results(self) -> bool:
        result = True

        print(f"\tFunction Liquidity Types:")
        for entry in (self.functions | self.events):
            self.functions_liq_type[entry] = entry.get_env()
            print(f"\t\t{entry}")
            print(f"\t\t\t{self.functions_liq_type[entry]['start']} -> {self.functions_liq_type[entry]['end']}")
            print(f"\t\t\t{entry.asset_types}")
            if isinstance(entry, FunctionVisitorEntry):
                print(f"\t\t\t{entry.events_list}")

        print(f"\tAbstract Computations:")
        for abs_computation in self.abs_computations:
            abs_comp_env = abs_computation.get_env()
            self.abs_computations_to_final_state.add(abs_computation)
            print(f"\t\t{abs_computation}")
            print(f"\t\t\t{abs_comp_env['start']} -> {abs_comp_env['end']}")
            print(f"\t\t\t{abs_computation.asset_types}")
            for h in abs_computation.liq_type_end[-1]:
                result = result and abs_computation.liq_type_end[-1][h] == LiqExpr(LiqConst.EMPTY)

        print("\tLiquidity Results:")
        self.compute_qq()
        self.compute_reachable_states()
        self.compute_tqk()
        print("\t\tCostly Algorithm:")
        print(f"\t\t\tis {'' if self.costly_algorithm_k_separate() else 'NOT '}k-separate liquid")
        print(f"\t\t\tis {'' if self.costly_algorithm_complete() else 'NOT '}liquid")

        if not self.abs_computations_to_final_state:
            return False
        return result


    # Definition 1 : constraint 1
    def compute_function_local_liquidity(self) -> tuple[bool, bool, bool]:
        for entry in self.functions:
            par = entry.compute_local_liquidity()
            if par:
                print(f"\t{entry}\n\t\tis NOT local liquid: {par}")
                return False, self.has_events, self.has_guards
        return True, self.has_events, self.has_guards


    def set_init_state_id(self, state_id):
        self.Q0 = state_id


    def add_party(self, party_id):
        self.parties.append(party_id)


    def add_visitor_function(self, visitor_entry: FunctionVisitorEntry, has_guard: bool = False):
        self.functions.add(visitor_entry)
        self.has_guards = self.has_guards | has_guard


    def add_visitor_event(self, visitor_entry: EventVisitorEntry):
        self.events.add(visitor_entry)
        self.has_events = True


    def add_global_asset(self, asset):
        self.global_assets.add(asset.text)


    def compute_r(self):
        # Base case
        # Initialize the dict foreach function
        # Value for 'f':
            # [f] if f starts from Q0
            # [] else
        for function in self.functions:
            if function.start_state == self.Q0:
                abs_computation = AbsComputation(function)
                for event in function.events_list:
                    abs_computation.add_available_event(event)
                self.abs_computations.add(abs_computation)

        is_change = True
        while is_change:
            is_change = False
            computations_to_add : set[AbsComputation] = set()
            for abs_computation in self.abs_computations:
                for function in self.functions:
                    if function.start_state == abs_computation.get_last_state():
                        new_abs_computation = abs_computation.copy_abs_computation()
                        if abs_computation.count(function) < K:
                            new_abs_computation.insert_configuration(function)
                        for event in function.events_list:
                            new_abs_computation.add_available_event(event)
                        computations_to_add.add(new_abs_computation)
                for event in abs_computation.available_events:
                    if event.start_state == abs_computation.get_last_state():
                        new_abs_computation = abs_computation.copy_abs_computation()
                        new_abs_computation.insert_configuration(event)
                        new_abs_computation.remove_available_event(event)
                        computations_to_add.add(new_abs_computation)

            is_change = is_change or bool(computations_to_add.difference(self.abs_computations))
            self.abs_computations.update(computations_to_add)

    def compute_qq(self):
        for state in self.states:
            self.Qq[state] = set()
        for entry in (self.functions | self.events):
            self.Qq[entry.start_state].add(entry)
        is_change = True
        while is_change:
            is_change = False
            for entry in (self.functions | self.events):
                prev_len = len(self.Qq[entry.start_state])
                self.Qq[entry.start_state] |= self.Qq[entry.end_state]
                self.Qq[entry.start_state].add(entry)
                if len(self.Qq[entry.start_state]) > prev_len:
                    is_change = True


    def compute_reachable_states(self):
        self.reachable_states.add(self.Q0)
        for entry in self.Qq[self.Q0]:
            self.reachable_states.add(entry.end_state)


    # TODO modificare sta roba perché fa schifo
    #   modificare compute_R includendo anche le abs_comp che non partano da Q0, così qui fai un ciclo for in meno senza quel copy_abs_comp
    def compute_tqk(self):
        for state in self.states:
            self.Tqk[state] = set()
        for abs_computation in self.abs_computations:
            for configuration in abs_computation:
                self.Tqk[configuration.start_state].add(abs_computation.copy_abs_computation(configuration.start_state))


    def compute_states(self):
        self.states = set()
        initial_states = set()
        for entry in (self.functions | self.events):
            self.states.add(entry.start_state)
            self.states.add(entry.end_state)
            initial_states.add(entry.start_state)
        self.final_states = self.states - initial_states


    def efficient_algorithm_k_separate(self) -> bool:
        # step 1
        self.compute_qq()
        z : set[tuple[str, str]] = set()

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
                        (entry.end_state, k) not in z
                    ):
                        found_missing_tuple = True
                        is_missing_tuple_added = False
                        # step 2.2
                        for next_entry in self.Qq[entry.end_state]:
                            next_entry_env = next_entry.get_env()
                            if next_entry_env['end'][k] == LiqExpr(LiqConst.EMPTY):
                                is_missing_tuple_added = True
                                z.add((entry.end_state, k))
                                break
                        if not is_missing_tuple_added:
                            print(f"\t\t\t\tEFFICIENT K-SEPARATE: {entry}, {k}")
                            return False
        # step 2.1
        return True


    def efficient_algorithm_complete(self) -> bool:
        # step 1
        z : set[str] = set()

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
                if h_not_zero and entry_env['start']!=entry_env['end'] and entry.end_state not in z:
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
                            z.add(entry.end_state)
                            break
                    if not is_missing_tuple_added:
                        print(f"\t\t\t\tEFFICIENT COMPLETE: {entry}")
                        return False
        # step 2.1
        return True


    def costly_algorithm_k_separate(self):
        for k in self.global_assets:
            z : set[str] = set()
            is_missing_state_found = True
            while is_missing_state_found:
                is_missing_state_found = False
                for state in self.reachable_states:
                    for abs_computation in self.Tqk[state]:
                        abs_computation_env = abs_computation.get_env()
                        if (abs_computation_env['end'][k] != LiqExpr(LiqConst.EMPTY) and
                            abs_computation_env['start'][k] != abs_computation_env['end'][k] and
                            abs_computation.get_last_state() not in z
                        ):
                            is_missing_state_found = True
                            is_missing_state_added = False
                            for abs_computation_p in self.Tqk[abs_computation.get_last_state()]:
                                abs_computation_p_env = abs_computation_p.get_env()
                                if abs_computation_p_env['end'][k] == LiqExpr(LiqConst.EMPTY):
                                    z.add(abs_computation.get_last_state())
                                    is_missing_state_added = True
                                    break
                            if not is_missing_state_added:
                                print(f"\t\t\t\tCOSTLY K-SEPARATE: {state}, {k}, {abs_computation}")
                                return False
        return True


    def costly_algorithm_complete(self):
        z : set[tuple[str,frozenset[str]]] = set()
        for state in self.reachable_states:
            for abs_computation in self.Tqk[state]:
                abs_computation_env = abs_computation.get_env()
                kbar = set()
                for k in self.global_assets:
                    if (abs_computation_env['end'][k] != LiqExpr(LiqConst.EMPTY)
                        and abs_computation_env['end'][k] != abs_computation_env['start'][k]
                        and (abs_computation.get_last_state(), frozenset({k})) not in z):
                        kbar.add(k)
                if kbar:
                    is_found = False
                    for abs_computation_p in self.Tqk[abs_computation.get_last_state()]:
                        is_abs_comp_valid = True
                        for k in kbar:
                            if abs_computation_p.get_env()['end'][k] != LiqExpr(LiqConst.EMPTY):
                                is_abs_comp_valid = False
                                break
                        if is_abs_comp_valid:
                            for h in self.global_assets - kbar:
                                if (abs_computation_p.get_env()['end'][h] != LiqExpr(LiqConst.EMPTY) and
                                    abs_computation_p.get_env()['start'][h] != abs_computation_p.get_env()['end'][h]):
                                    is_abs_comp_valid = False
                                    break
                        if is_abs_comp_valid:
                            z.add((abs_computation_p.get_last_state(), frozenset(kbar)))
                            is_found = True
                            break
                    if not is_found:
                        print(f"\t\t\t\tCOSTLY COMPLETE: {abs_computation} {kbar}")
                        return False
                else:
                    return True
        return True