class AssetTypes:
    def __init__(self):
        self.type_groups : set[frozenset[str]] = set()

    def add_singleton(self, h: str) -> None:
        """
        :param h: asset name to add
        """
        self.type_groups.add(frozenset([h]))

    def merge_types(self, a: str, b:str) -> bool:
        """
        :param a: asset name to merge
        :param b: asset name to merge
        :return: False if any errors occurred, else True
        """
        set_a = None
        set_b = None

        for s in self.type_groups:
            if a in s:
                set_a = s
            if b in s:
                set_b = s

        if set_a is None or set_b is None:
            print("ERROR merge_asset_types")
            return False

        if set_a is set_b:
            return True

        merged = frozenset(set_a | set_b)

        self.type_groups.remove(set_a)
        self.type_groups.remove(set_b)
        self.type_groups.add(merged)
        return True

    def __iter__(self):
        return iter(self.type_groups)

    def __str__(self):
        result = ''
        for g in self.type_groups:
            result += '('
            for e in g:
                result += f"{e}, "
            result = result[:-2] + '); '
        return result[:-2]
    __repr__ = __str__
