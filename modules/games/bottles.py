from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

@dataclass(frozen=True)
class GameItem:
    key: str
    label: str
    source: str
    meta: dict[str, Any]

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


def get_bottle_games() -> dict[str, GameItem]:
    programs: dict[str, GameItem] = {}
    seen: set[str] = set()

    for bottle_file in _find_bottle_files():
        data = _load_yaml(bottle_file)
        bottle_name = _extract_bottle_name(data)
        for name in _extract_external_program_names(data):
            if name not in seen:
                seen.add(name)
                key = f"bottles:{bottle_name}:{name}"
                programs[key] = GameItem(
                    key=key,
                    label=name,
                    source="bottles",
                    meta={"bottle": bottle_name, "prog": name},
                )

    return programs
