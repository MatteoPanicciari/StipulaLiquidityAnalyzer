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
            function_type_output_result[el] = self.get_current_field_value(el)
        return {'in': self.function_type_input, 'out': function_type_output_result}

    def __str__(self):
        return f"{self.start_state} {self.handler}:{self.code_id} {self.end_state};"
    def __repr__(self):
        return f"{self.start_state} {self.handler}.{self.code_id} {self.end_state}"

class EventVisitorEntry(VisitorEntry):
    def __str__(self):
        return f"ev{VisitorEntry.__str__(self)}"