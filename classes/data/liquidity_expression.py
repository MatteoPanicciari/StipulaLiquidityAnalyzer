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
            old_node = self.copy()
            self.left = old_node
            self.right = right
            self.value = operation
        else:
            print("ERROR set_operation")

    def replace_value(self, start_value: str, end_value: LiqExpr):
        if self.value in LiqConst.operators and self.left and self.right:
            self.left.replace_value(start_value, end_value)
            self.right.replace_value(start_value, end_value)
        elif self.value == start_value:
            new_node = end_value.copy()
            self.value = new_node.value
            self.left = new_node.left
            self.right = new_node.right

    def __str__(self):
        if self.left is None or self.right is None:
            return self.value
        return f'({self.left} {self.value} {self.right})'

    __repr__ = __str__

    def __eq__(self, other):
        if isinstance(other, LiqExpr):
            return self.value == other.value and self.left == other.left and self.right == other.right
        return False

    def copy(self) -> LiqExpr:
        return LiqExpr(self.value, self.left, self.right)