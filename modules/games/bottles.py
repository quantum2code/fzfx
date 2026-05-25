from pathlib import Path
import subprocess
from typing import Any
import yaml
from modules.core import Module, SearchItem

         
class BottlesModule(Module):
    def __init__(self) -> None:
        super().__init__()

    def get_list(self) -> list[SearchItem]:
        return get_bottle_games()
 
    def take_action(self, item: SearchItem):
        subprocess.run([
            "bottles-cli",
            "run",
            "-b",
            item.meta["bottle"],
            "-p",
            item.meta["prog"],
        ])

def _find_bottle_files(base_dir: Path | None = None) -> list[Path]:
    root = base_dir or (Path.home() / ".local")
    if not root.exists():
        return []
    return sorted(root.rglob("bottle.yml"))


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except OSError:
        return {}

    return data if isinstance(data, dict) else {}


def _extract_bottle_name(data: dict[str, Any]) -> str:
    name = data.get("Name", "")
    return name if isinstance(name, str) else ""
def _extract_external_program_names(data: dict[str, Any]) -> list[str]:
    external_programs = data.get("External_Programs", {})
    if not isinstance(external_programs, dict):
        return []

    names: list[str] = []
    for program in external_programs.values():
        if not isinstance(program, dict):
            continue

        name = program.get("name")
        if isinstance(name, str) and name.strip():
            names.append(name)

    return names


def get_bottle_games() -> list[SearchItem]:
    programs: list[SearchItem] = []
    seen: set[str] = set()

    for bottle_file in _find_bottle_files():
        data = _load_yaml(bottle_file)
        bottle_name = _extract_bottle_name(data)
        for name in _extract_external_program_names(data):
            if name not in seen:
                seen.add(name)
                programs.append(SearchItem(
                    key=f"bottles:{bottle_name}:{name}",
                    type="game",
                    label=name,
                    meta={"bottle": bottle_name, "source": "bottles", "prog": name},
                ))

    return programs
