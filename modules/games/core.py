from modules.core import Module, SearchItem
from modules.games.bottles import BottlesModule


class GameModule(Module):
    def __init__(self) -> None:
        super().__init__()
        self.modules: dict[str, Module] = {"bottles": BottlesModule()}
        self.data: list[SearchItem] = []

    def get_list(self) -> list[SearchItem]:
        if self.data:
            return self.data
        for m in self.modules.values():
            self.data.extend(m.get_list())
        return self.data

    def take_action(self, item: SearchItem):
        module = self.modules.get(item.meta["source"])
        if module:
            module.take_action(item)
