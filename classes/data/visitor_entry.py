from classes.data.asset_types import AssetTypes
from classes.data.liquidity_expression import LiqExpr, LiqConst

class VisitorEntry:
    xi_count : int = 1

    def __init__(self, start_state: str, end_state: str, global_assets: list[str]):
        self.start_state: str = start_state
        self.end_state: str = end_state

        self.input_env: dict[str, LiqExpr] = dict()
        # Symbol Table - Lists' Hashtable (Chapter 4.2)
        # For each asset, we have a list of LiqExpr
        # Each element of the list represents a level for the nested blocks
        # If LiqExpr is none, the level to consider is the previous one
        self.output_env: dict[str, list[LiqExpr | None]] = dict()

        self.global_assets: list[str] = global_assets

        self.asset_types: AssetTypes = AssetTypes()

        for h in global_assets:
            # initialize global assets value to XI
            self.input_env[h] = LiqExpr(f'{LiqConst.XI}{self.xi_count}')
            self.output_env[h] = [LiqExpr(f'{LiqConst.XI}{self.xi_count}')]
            self.xi_count += 1
            self.asset_types.add_singleton(h)

    # region environment levels
    def add_env_level(self) -> None:
        for el in self.output_env:
            self.output_env[el].append(None)

    def del_env_level(self) -> None:
        for el in self.output_env:
            self.output_env[el].pop()
    # endregion environment levels


    # region getter setter
    def set_field_value(self, field: str, value: LiqExpr) -> None:
        self.output_env[field][-1] = value

    def get_start_state(self) -> str:
        return self.start_state

    def get_end_state(self) -> str:
        return self.end_state

    def get_output_type(self) -> dict[str, list[LiqExpr | None]]:
        return self.output_env

    def get_asset_types(self) -> AssetTypes:
        return self.asset_types

    def merge_function_asset_types(self, first: str, second: str) -> None:
        self.asset_types.merge_types(first, second)

    def get_global_assets(self) -> list[str]:
        return self.global_assets

    def get_current_field_value(self, field: str) -> LiqExpr | None:
        """
        :param field: name of the field whose value you want to know
        :return: the last non-None value of the field value list. None if the field does not contain any LiqExpr value
        """
        count = 1
        res = None
        while not res and count <= len(self.output_env[field]):
            res = self.output_env[field][-count]
            count+=1
        return res

    def get_env(self) -> dict[str, dict[str,LiqExpr]]:
        output_type_result = {}
        for el in self.output_env:
            output_type_result[el] = LiqExpr.resolve_partial_eval(self.get_current_field_value(el))
        return {'start': self.input_env, 'end': output_type_result}
    # endregion getter setter

    def copy_global_env(self) -> dict[str, dict[str, LiqExpr]]:
        entry_type = self.get_env()
        entry_type_result = dict(start=dict(), end=dict())
        for el in self.global_assets:
            entry_type_result['start'][el] = entry_type['start'][el].copy_liquidity()
            entry_type_result['end'][el] = entry_type['end'][el].copy_liquidity()
        return entry_type_result


class EventVisitorEntry(VisitorEntry):
    def __init__(self, trigger: str, start_state: str, end_state: str, global_assets: list[str]):
        super().__init__(start_state, end_state, global_assets)
        self.trigger: str = trigger

    def __str__(self):
        return f"{self.start_state} {self.trigger} {self.end_state}"
    __repr__ = __str__


class FunctionVisitorEntry(VisitorEntry):
    def __init__(self, start_state: str, handler: str, code_id: str, end_state: str,
                 global_assets: list[str], local_assets: set[str], has_guard: bool):
        super().__init__(start_state, end_state, global_assets)
        self.code_id: str = code_id
        self.handler: str = handler

        self.local_assets: set[str] = local_assets
        self.has_guard: bool = has_guard

        self.events_list: list[EventVisitorEntry] = []

        for p in local_assets:
            # initialize local assets value to FULL
            self.input_env[p] = LiqExpr(LiqConst.FULL)
            self.output_env[p] = [LiqExpr(LiqConst.FULL)]
            self.asset_types.add_singleton(p)

    def compute_local_liquidity(self) -> list[str]:
        """
            Check local assets to see if they are all emptied during the function

            :return: list of the assets not emptied
        """
        result = []
        env_end = self.get_env()['end']
        for p in self.local_assets:
            if not env_end[p] == LiqExpr(LiqConst.EMPTY):
                result.append(p)
        return result

    def add_event(self, event: EventVisitorEntry) -> None:
        """
            Add an event to the events list of the function.
        """
        self.events_list.append(event)

    def __str__(self):
        return f"{self.start_state} {self.handler}:{self.code_id} {self.end_state}"
    __repr__ = __str__