from dataclasses import dataclass
from typing import Any
import logging

logging.basicConfig(
    filename="fzfx-debug.log",
    filemode="a",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


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
