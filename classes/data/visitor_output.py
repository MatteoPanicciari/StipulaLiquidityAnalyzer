from classes.data.abstract_computation import AbsComputation
from classes.data.visitor_entry import FunctionVisitorEntry
from classes.data.liquidity_expression import LiqExpr, LiqConst

K: int = 2 # maximum number of times a function can appear in the same abstract computation (k-canonical)

class VisitorOutput:
    def __init__(self):
        self.Q0 : str = ''  # initial state
        self.parties: list[str] = list()
        self.global_assets: list[str] = list()
        self.functions: set[FunctionVisitorEntry] = set() # set of all the clauses of the contract
        self.abs_computations: dict[FunctionVisitorEntry, set[AbsComputation]] = dict()
        self.final_states: list[str] = list()

        self.abs_computations_to_final_state : set[AbsComputation] = set()
        self.functions_liq_type : dict[FunctionVisitorEntry, dict[str, dict[str, LiqExpr]]] = dict()
        self.abs_computations_liq_type : dict[AbsComputation, tuple[str, dict[str, LiqExpr]]] = dict()

    def compute_results(self, name) -> bool:
        print(f"_________________________________________\n{name}")
        result = True

        print(f"\tFunction Liquidity Types:")
        for fn in self.functions:
            self.functions_liq_type[fn] = fn.get_function_type()
            print(f"\t\t{fn} : {self.functions_liq_type[fn]['start']} -> {self.functions_liq_type[fn]['end']}")

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
            return False

        return result


    def set_init_state_id(self, state_id):
        self.Q0 = state_id

    def add_party(self, party_id):
        self.parties.append(party_id)

    def add_visitor_entry(self, visitor_entry):
        self.functions.add(visitor_entry)

    def add_global_asset(self, asset):
        self.global_assets.append(asset.text)

    def compute_r(self):
        # Base case
        # Initialize the dict foreach function
        # Value for 'f':
            # [f] if f starts from Q0
            # [] else
        for visitor_entry in self.functions:
            if isinstance(visitor_entry, FunctionVisitorEntry) and visitor_entry.start_state == self.Q0:
                self.abs_computations[visitor_entry] = { AbsComputation(visitor_entry) }
            else:
                self.abs_computations[visitor_entry] = set()

        is_change = True
        while is_change:
            is_change = False
            for current_fn in self.functions:
                set_tuples_to_add = set()
                for previous_fn in self.functions:
                    # checks if previous_fn goes to current_function start state
                    if previous_fn.end_state == current_fn.start_state:
                        for previous_fn_abs_computation in self.abs_computations[previous_fn]:
                            # foreach tuple in previous_fn.set:
                            #   checks if the current function appears less than k times in the tuple
                            #   if True, add the function to the tuple
                            new_previous_fn_tuple = previous_fn_abs_computation.copy_abs_computation()
                            if previous_fn_abs_computation.count(current_fn) < K:
                                new_previous_fn_tuple.insert_function(current_fn)
                            set_tuples_to_add.add(new_previous_fn_tuple)

                is_change = is_change or bool(set_tuples_to_add.difference(self.abs_computations[current_fn]))
                self.abs_computations[current_fn].update(set_tuples_to_add)

    def compute_final_states(self):
        states = set()
        initial_states = set()
        for visitor_entry in self.functions:
            if type(visitor_entry).__name__ == FunctionVisitorEntry.__name__:
                states.add(visitor_entry.start_state)
                states.add(visitor_entry.end_state)
                initial_states.add(visitor_entry.start_state)
        self.final_states = states - initial_states
