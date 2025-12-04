from __future__ import annotations
from typing import Optional

class LiqConst:
    upper_operator : str = 'u'
    lower_operator : str = 'n'
    operators = [upper_operator, lower_operator]
    empty : str = '0'
    full : str = '1'
    constants = [empty, full]
    xi : str = 'ξ'

class LiqExpr:
    def __init__(self, value: str, left:LiqExpr=None, right:LiqExpr=None):
        self.value: str = value
        self.left: Optional[LiqExpr] = left
        self.right: Optional[LiqExpr] = right

    def add_operation(self, operation: str, right: LiqExpr):
        if operation in LiqConst.operators:
            old_node = LiqExpr(self.value, self.left, self.right)
            self.left = old_node
            self.right = right
            self.value = operation
        else:
            print("ERROR set_operation")

    def __str__(self):
        if self.left is None or self.right is None:
            return self.value
        return f'({self.left} {self.value} {self.right})'

    __repr__ = __str__

    def __eq__(self, other):
        if isinstance(other, LiqExpr):
            return self.value == other.value and self.left == other.left and self.right == other.right
        return False

class CodeReference:
    def __init__(self, start_line, end_line):
        self.start_line = start_line
        self.end_line = end_line

class VisitorEntry:
    def __init__(self, start_state, handler, code_id, end_state, code_reference: CodeReference):
        self.start_state = start_state
        self.handler = handler
        self.code_id = code_id
        self.end_state = end_state
        self.code_reference = code_reference

class FunctionVisitorEntry(VisitorEntry):
    xi_count : int = 1
    def __init__(self, start_state, handler, code_id, end_state, code_reference, xi, ones):
        super().__init__(start_state, handler, code_id, end_state, code_reference)

        self.function_type_input: dict[str, LiqExpr] = {}
        self.function_type_output: dict[str, list[LiqExpr | None]] = {}

        for h in xi:
            self.function_type_input[h] = LiqExpr(f'{LiqConst.xi}{self.xi_count}')
            self.function_type_output[h] = [LiqExpr(f'{LiqConst.xi}{self.xi_count}')]
            self.xi_count += 1

        for p in ones:
            self.function_type_input[p] = LiqExpr(LiqConst.full)
            self.function_type_output[p] = [LiqExpr(LiqConst.full)]

    def add_function_level(self):
        for el in self.function_type_output:
            self.function_type_output[el].append(None)

    def del_function_level(self):
        for el in self.function_type_output:
            self.function_type_output[el].pop()

    def set_field_value(self, field: str, value: LiqExpr):
        self.function_type_output[field][-1] = value

    def get_current_field_value(self, field) -> LiqExpr:
        count = 1
        res = None
        while not res and count <= len(self.function_type_output[field]):
            res = self.function_type_output[field][-count]
            count+=1
        return res

    def get_function_type(self) -> dict[str, dict[str,LiqExpr]]:
        function_type_output_result = {}
        for el in self.function_type_output:
            function_type_output_result[el] = self.resolve_partial_evaluation(self.get_current_field_value(el))
        return {'in': self.function_type_input, 'out': function_type_output_result}

    def resolve_partial_evaluation(self, e: LiqExpr) -> LiqExpr:
        if e.value in LiqConst.constants or LiqConst.xi in e.value:
            # if e=0 or e=1 or e=ξ
            return LiqExpr(e.value)

        e_left = self.resolve_partial_evaluation(e.left)
        e_right = self.resolve_partial_evaluation(e.right)
        if e.value == LiqConst.upper_operator:
            # if   e = e' u e''   and   (e' = 1   or   e'' = 1)
            if e_left == LiqExpr(LiqConst.full) or e_right == LiqExpr(LiqConst.full):
                return LiqExpr(LiqConst.full)

            # if   (e = e' u e''   or   e = e'' u e')   and   e'' = 0
            if e_left == LiqExpr(LiqConst.empty):
                return e_right
            if e_right == LiqExpr(LiqConst.empty):
                return e_left

            # if   e = e' u e''   and no-one of the above cases applies
            return LiqExpr(LiqConst.upper_operator, e_left, e_right)
        elif e.value == LiqConst.lower_operator:
            # if   e = e' n e''   and   (e' = 0   or   e'' = 0)
            if e_left == LiqExpr(LiqConst.empty) or e_right == LiqExpr(LiqConst.empty):
                return LiqExpr(LiqConst.empty)

            # if   (e = e' n e''   or   e = e'' n e')   and   e'' = 1
            if e_left == LiqExpr(LiqConst.full):
                return e_right
            if e_right == LiqExpr(LiqConst.full):
                return e_left

            # if   e = e' u e''   and no-one of the above cases applies
            return LiqExpr(LiqConst.lower_operator, e_left, e_right)

        print("ERROR resolve_partial_evaluation")
        return e



    def __str__(self):
        return f"{self.start_state} {self.handler}:{self.code_id} {self.end_state};"
    def __repr__(self):
        return f"{self.start_state} {self.handler}.{self.code_id} {self.end_state}"

class EventVisitorEntry(VisitorEntry):
    def __str__(self):
        return f"ev{VisitorEntry.__str__(self)}"