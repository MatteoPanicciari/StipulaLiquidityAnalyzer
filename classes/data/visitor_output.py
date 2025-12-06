import functools

from classes.data.visitor_entry import FunctionVisitorEntry
from classes.data.liquidity_expression import LiqExpr
from collections import Counter

NOW = 'now'

class VisitorOutput:
    k = 1   # maximum number of times a function can appear in the same abstract computation (k-canonical)

    def __init__(self):
        self.Q0 : str = ''  # initial state
        self.parties: list[str] = list()
        self.global_assets: list[str] = list()
        self.functions: set[FunctionVisitorEntry] = set() # set of all the clauses of the contract
        self.abs_computations: dict[FunctionVisitorEntry, set[tuple[FunctionVisitorEntry]]] = dict()
        self.final_states: list[str] = list()

        self.abs_computations_to_final_state : set[tuple[FunctionVisitorEntry]] = set()
        self.functions_liq_type : dict[FunctionVisitorEntry, dict[str, dict[str, LiqExpr]]] = dict()
        self.abs_computations_liq_type : dict[tuple[FunctionVisitorEntry], tuple[str, dict[str, LiqExpr]]] = dict()

    def compute_results(self, name):
        print(f"_________________________________________\n{name}")

        print(f"\tFunction Liquidity Types:")
        for fn in self.functions:
            self.functions_liq_type[fn] = fn.get_function_type()
            print(f"\t\t{fn} : {self.functions_liq_type[fn]['in']} -> {self.functions_liq_type[fn]['out']}")

        print(f"\tAbstract Computations to Final States:")
        for fn in self.abs_computations:
            if fn.end_state in self.final_states:
                for abs_computation in self.abs_computations[fn]:
                    self.abs_computations_to_final_state.add(abs_computation)
                    print(f"\t\t{self.print_formatted_computation(abs_computation)}")

    @staticmethod
    def print_formatted_computation(computation):
        result = ''
        for configuration in computation:
            result+=str(configuration)
        return result

    def set_init_state_id(self, state_id):
        self.Q0 = state_id

    def add_party(self, party_id):
        self.parties.append(party_id)

    def add_visitor_entry(self, visitor_entry):
        self.functions.add(visitor_entry)

    def add_global_asset(self, asset):
        self.global_assets.append(asset.text)

    def is_cyclic(self, visitor_entry, loop_visitor_entry_set, visitor_entry_set):
        if visitor_entry in loop_visitor_entry_set:
            return True
        visitor_entry_set = visitor_entry_set or functools.reduce(lambda a, b: a.union(set(b)), functools.reduce(lambda a, b: a.union(b), self.abs_computations.values(), set()), set())
        for previous_visitor_entry in (previous_visitor_entry for previous_visitor_entry in visitor_entry_set if previous_visitor_entry.end_state == visitor_entry.start_state):
            if self.is_cyclic(previous_visitor_entry, loop_visitor_entry_set.union({
                visitor_entry
            }), visitor_entry_set):
                return True
        return False

    def compute_r(self):
        # Base case
        # Initialize the dict foreach function
        # Value for 'f':
            # [f] if f starts from Q0
            # [] else
        for visitor_entry in self.functions:
            if isinstance(visitor_entry, FunctionVisitorEntry) and visitor_entry.start_state == self.Q0:
                self.abs_computations[visitor_entry] = {(visitor_entry,)}
            else:
                self.abs_computations[visitor_entry] = set()

        is_change = True
        while is_change:
            is_change = False
            for current_fn in self.functions:
                tuples_to_add = set()
                for previous_fn in self.functions:
                    if previous_fn.end_state == current_fn.start_state:
                        # check if previous_fn goes to current_function start state
                        for previous_fn_tuple in self.abs_computations[previous_fn]:
                            # foreach tuple in previous_fn.set:
                            #   checks if the current function appears less than k times in the tuple
                            #   if True, add the function to the tuple
                            new_previous_fn_tuple = previous_fn_tuple
                            if Counter(previous_fn_tuple)[current_fn] < self.k:
                                new_previous_fn_tuple += (current_fn,)
                            tuples_to_add.add(new_previous_fn_tuple)

                is_change = is_change or bool(tuples_to_add.difference(self.abs_computations[current_fn]))
                self.abs_computations[current_fn].update(tuples_to_add)

    def compute_final_states(self):
        states = set()
        initial_states = set()
        for visitor_entry in self.functions:
            if type(visitor_entry).__name__ == FunctionVisitorEntry.__name__:
                states.add(visitor_entry.start_state)
                states.add(visitor_entry.end_state)
                initial_states.add(visitor_entry.start_state)
        self.final_states = states - initial_states
