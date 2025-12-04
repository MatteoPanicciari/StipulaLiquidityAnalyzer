import functools

from classes.data.visitorentry import FunctionVisitorEntry

NOW = 'now'

class VisitorOutput:
    k = 1

    def __init__(self):
        self.Q0 : str = ''  # initial state
        self.parties: list[str] = list()
        self.global_assets: list[str] = list()
        self.functions: set[FunctionVisitorEntry] = set() # set of all the clauses of the contract
        # TODO: trasformarli in dei multiset per poter far sì che una funzione compaia
        #  in una computazione al più un numero k di volte e non 1 come adesso
        self.abs_computations: dict[FunctionVisitorEntry, tuple[FunctionVisitorEntry]] = dict()
        self.final_states: list[str] = list()

    def print_results(self):
        print("_________________________________________\nRESULTS")

        results=[]
        for a in self.abs_computations:
            if a.end_state in self.final_states:
                for b in self.abs_computations[a]:
                    results.append(self.print_formatted_computation(b))
        print(f"\nabstract computations to final states:")
        for a in results:
            print(a)

        lc = dict()
        for a in self.functions:
            lc[a] = a.get_function_type()
        print(f"\nLc:")
        for a in lc:
            print(f"{a} : {lc[a]['in']} -> {lc[a]['out']}")

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
            for current_visitor_entry in self.functions:
                visitor_entry_tuple_set_to_add = set()
                if type(current_visitor_entry).__name__ ==  FunctionVisitorEntry.__name__:
                    for previous_visitor_entry in self.functions:
                        # check if the previous_entry end state match with current_entry start state
                        if previous_visitor_entry.end_state == current_visitor_entry.start_state:
                            # foreach tuple of previous_entry computations, checks if current_entry is already in the tuple
                            for visitor_entry_tuple in self.abs_computations[previous_visitor_entry]:
                                if current_visitor_entry not in visitor_entry_tuple:
                                    new_tuple = visitor_entry_tuple + (current_visitor_entry,)
                                else:
                                    new_tuple = visitor_entry_tuple

                                visitor_entry_tuple_set_to_add.add(new_tuple)

                is_change = is_change or bool(visitor_entry_tuple_set_to_add.difference(self.abs_computations[current_visitor_entry]))
                self.abs_computations[current_visitor_entry].update(visitor_entry_tuple_set_to_add)

    def compute_final_states(self):
        states = set()
        initial_states = set()
        for visitor_entry in self.functions:
            if type(visitor_entry).__name__ == FunctionVisitorEntry.__name__:
                states.add(visitor_entry.start_state)
                states.add(visitor_entry.end_state)
                initial_states.add(visitor_entry.start_state)
        self.final_states = states - initial_states
