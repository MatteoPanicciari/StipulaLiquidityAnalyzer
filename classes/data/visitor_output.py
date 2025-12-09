from classes.data.abstract_computation import AbsComputation
from classes.data.visitor_entry import FunctionVisitorEntry, EventVisitorEntry
from classes.data.liquidity_expression import LiqExpr, LiqConst

K: int = 2
# maximum number of times a function can appear in the same abstract computation (k-canonical)

class VisitorOutput:
    def __init__(self):
        self.Q0 : str = ''  # initial state
        self.parties: list[str] = list()
        self.global_assets: list[str] = list()
        self.entries: set[FunctionVisitorEntry] = set() # set of all the clauses of the contract
        self.abs_computations: dict[FunctionVisitorEntry, set[AbsComputation]] = dict()
        self.final_states: list[str] = list()

        self.abs_computations_to_final_state : set[AbsComputation] = set()
        self.functions_liq_type : dict[FunctionVisitorEntry, dict[str, dict[str, LiqExpr]]] = dict()
        self.abs_computations_liq_type : dict[AbsComputation, tuple[str, dict[str, LiqExpr]]] = dict()

        self.has_events: bool = False
        self.has_guards: bool = False

    def compute_results(self, name) -> tuple[bool, bool, bool]:
        print(f"_________________________________________\n{name}")
        result = True

        print(f"\tFunction Liquidity Types:")
        for entry in self.entries:
            self.functions_liq_type[entry] = entry.get_env()
            print(f"\t\t{entry}")
            print(f"\t\t\t{self.functions_liq_type[entry]['start']} -> {self.functions_liq_type[entry]['end']}")
            print(f"\t\t\t{entry.asset_types}")

        print(f"\tAbstract Computations to Final States:")
        for fn in self.abs_computations:
            if fn.end_state in self.final_states:
                for abs_computation in self.abs_computations[fn]:
                    self.abs_computations_to_final_state.add(abs_computation)
                    print(f"\t\t{abs_computation}")
                    print(f"\t\t\t{abs_computation.liq_type_begin[0]} -> {abs_computation.liq_type_end[-1]}")
                    for h in abs_computation.liq_type_end[-1]:
                        result = result and abs_computation.liq_type_end[-1][h] == LiqExpr(LiqConst.EMPTY)

        if not self.abs_computations_to_final_state:
            return False, self.has_events, self.has_guards

        return result, self.has_events, self.has_guards


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

    def compute_final_states(self):
        states = set()
        initial_states = set()
        for visitor_entry in self.entries:
            if type(visitor_entry).__name__ == FunctionVisitorEntry.__name__:
                states.add(visitor_entry.start_state)
                states.add(visitor_entry.end_state)
                initial_states.add(visitor_entry.start_state)
        self.final_states = states - initial_states
