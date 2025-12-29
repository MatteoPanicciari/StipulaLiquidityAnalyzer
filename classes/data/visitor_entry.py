from classes.data.asset_types import AssetTypes
from classes.data.liquidity_expression import LiqExpr, LiqConst

class VisitorEntry:
    xi_count : int = 1

    def __init__(self, start_state, end_state, global_assets):
        self.start_state : str = start_state
        self.end_state : str = end_state

        self.input_type: dict[str, LiqExpr] = {}
        self.output_type: dict[str, list[LiqExpr | None]] = {}

        self.global_assets : set[str] = global_assets

        self.asset_types : AssetTypes = AssetTypes()

        for h in global_assets:
            self.input_type[h] = LiqExpr(f'{LiqConst.XI}{self.xi_count}')
            self.output_type[h] = [LiqExpr(f'{LiqConst.XI}{self.xi_count}')]
            self.xi_count += 1
            self.asset_types.add_singleton(h)

    # region environment levels
    def add_env_level(self):
        for el in self.output_type:
            self.output_type[el].append(None)

    def del_env_level(self):
        for el in self.output_type:
            self.output_type[el].pop()
    # endregion environment levels


    # region getter setter
    def set_field_value(self, field: str, value: LiqExpr):
        self.output_type[field][-1] = value

    def get_start_state(self) -> str:
        return self.start_state

    def get_end_state(self) -> str:
        return self.end_state

    def get_output_type(self) -> dict[str, list[LiqExpr | None]]:
        return self.output_type

    def get_asset_types(self) -> AssetTypes:
        return self.asset_types

    def get_global_assets(self) -> set[str]:
        return self.global_assets

    def get_current_field_value(self, field) -> LiqExpr:
        count = 1
        res = None
        while not res and count <= len(self.output_type[field]):
            res = self.output_type[field][-count]
            count+=1
        return res

    def get_env(self) -> dict[str, dict[str,LiqExpr]]:
        output_type_result = {}
        for el in self.output_type:
            output_type_result[el] = LiqExpr.resolve_partial_eval(self.get_current_field_value(el))
        return {'start': self.input_type, 'end': output_type_result}
    # endregion getter setter

    def copy_global_env(self) -> dict[str, dict[str, LiqExpr]]:
        entry_type = self.get_env()
        entry_type_result = dict(start=dict(), end=dict())
        for el in self.global_assets:
            entry_type_result['start'][el] = entry_type['start'][el].copy_liquidity()
            entry_type_result['end'][el] = entry_type['end'][el].copy_liquidity()
        return entry_type_result


class EventVisitorEntry(VisitorEntry):
    def __init__(self, trigger, start_state, end_state, global_assets):
        super().__init__(start_state, end_state, global_assets)
        self.trigger = trigger

    def __str__(self):
        return f"{self.start_state} {self.trigger} {self.end_state}"
    __repr__ = __str__


class FunctionVisitorEntry(VisitorEntry):
    def __init__(self, start_state, handler, code_id, end_state, global_assets, local_assets, has_guard):
        super().__init__(start_state, end_state, global_assets)
        self.code_id = code_id
        self.handler = handler

        self.local_assets = local_assets
        self.has_guard = has_guard

        self.events_list : list[EventVisitorEntry] = []

        for p in local_assets:
            self.input_type[p] = LiqExpr(LiqConst.FULL)
            self.output_type[p] = [LiqExpr(LiqConst.FULL)]
            self.asset_types.add_singleton(p)

    def compute_local_liquidity(self) -> list[str]:
        result = []
        env_end = self.get_env()['end']
        for p in self.local_assets:
            if not env_end[p] == LiqExpr(LiqConst.EMPTY):
                result.append(p)
        return result

    def __str__(self):
        return f"{self.start_state} {self.handler}:{self.code_id} {self.end_state}"
    __repr__ = __str__

    def add_event(self, event: EventVisitorEntry):
        self.events_list.append(event)