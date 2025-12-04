class LiquidityExpression:
    def __init__(self, v: str):
        self.value : str = v

    def set_liquidity_value(self, v: int, right: str = ''):
        match v:
            case 0:
                self.value = '0'
            case 1:
                self.value = '1'
            case 3:
                self.value = f'{right}'
            case -1:
                self.value = f'({self.value} u {right})'
            case -2:
                self.value = f'({self.value} n {right})'
            case -3:
                self.value = f'UNSET'

    def __repr__(self):
        return self.value
    def __str__(self):
        return self.value

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