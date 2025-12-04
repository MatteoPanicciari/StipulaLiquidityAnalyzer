from __future__ import annotations
from typing import Optional

class LiquidityConstants:
    upper_operator : str = 'u'
    lower_operator : str = 'n'
    operators = [upper_operator, lower_operator]
    empty : str = '0'
    full : str = '1'
    constants = [empty, full]
    xi : str = 'ξ'

class LiquidityExpression:
    def __init__(self, value: str, left:LiquidityExpression=None, right:LiquidityExpression=None):
        self.value: str = value
        self.left: Optional[LiquidityExpression] = left
        self.right: Optional[LiquidityExpression] = right

    def set_operation(self, operation: str, right: LiquidityExpression):
        if operation in LiquidityConstants.operators:
            old_node = LiquidityExpression(self.value, self.left, self.right)
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

    def __str__(self):
        return str((
            self.start_state,
            self.handler,
            self.code_id,
            self.end_state,
        ))

class FunctionVisitorEntry(VisitorEntry):
    xi_count : int = 1
    def __init__(self, start_state, handler, code_id, end_state, code_reference, xi, ones):
        super().__init__(start_state, handler, code_id, end_state, code_reference)

        self.function_type_input: dict[str, LiquidityExpression] = {}
        self.function_type_output: dict[str, list[LiquidityExpression]] = {}
        self.assets: list[str] = []
        self.params: list[str] = []

        for h in xi:
            self.function_type_input[h] = LiquidityExpression(f'ξ{self.xi_count}')
            self.function_type_output[h] = [LiquidityExpression(f'ξ{self.xi_count}')]
            self.xi_count += 1
            self.assets.append(h)

        for p in ones:
            self.function_type_input[p] = LiquidityExpression('1')
            self.function_type_output[p] = [LiquidityExpression('1')]
            self.params.append(p)

    def add_function_level(self):
        for el in self.function_type_output:
            self.function_type_output[el].append(LiquidityExpression('UNSET'))

    def del_function_level(self):
        for el in self.function_type_output:
            self.function_type_output[el].pop()

    def set_output(self, field, value:int, right:str=''):
        if value < 0:
            if right:
                right_value = self.get_output(right)
            else:
                print('ERROR set_output')
                return
        else:
            right_value = right
        self.function_type_output[field][-1].set_liquidity_value(value, right_value)

    def get_output(self, field):
        count = 1
        res = 'UNSET'
        while res == 'UNSET' and count <= len(self.function_type_output[field]):
            res = self.function_type_output[field][-count].value
            count+=1
        return res

    def get_function_type(self):
        function_type_output_result = {}
        for el in self.function_type_output:
            function_type_output_result[el] = self.get_output(el)
        return {'in': self.function_type_input, 'out': function_type_output_result}

    def __str__(self):
        return f"{self.start_state} {self.handler}:{self.code_id} {self.end_state};"
    def __repr__(self):
        return f"{self.start_state} {self.handler}.{self.code_id} {self.end_state}"

class EventVisitorEntry(VisitorEntry):
    def __str__(self):
        return f"ev{VisitorEntry.__str__(self)}"