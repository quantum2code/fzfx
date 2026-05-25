from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class SearchItem:
    key: str
    type: str
    label: str
    meta: dict[str, Any]


class Module:
    def __init__(self) -> None:
        pass

    def get_list(self) -> list[SearchItem]:
        return []

    def take_action(self, item: SearchItem):
        pass
