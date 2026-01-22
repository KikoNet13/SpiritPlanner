from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class AdversaryLevel:
    level: str
    difficulty: int


@dataclass(frozen=True)
class AdversaryInfo:
    adversary_id: str
    name: str
    levels: tuple[AdversaryLevel, ...]


def _data_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "pc" / "data" / "input"


def _load_tsv_rows(filename: str, required_fields: Iterable[str]) -> list[dict[str, str]]:
    path = _data_dir() / filename
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames:
            return []
        if any(field not in reader.fieldnames for field in required_fields):
            return []
        return [row for row in reader if all(row.get(field) for field in required_fields)]


@lru_cache
def _load_simple_map(filename: str, key_field: str, value_field: str) -> dict[str, str]:
    rows = _load_tsv_rows(filename, [key_field, value_field])
    return {
        row[key_field].strip(): row[value_field].strip()
        for row in rows
        if row.get(key_field) and row.get(value_field)
    }


def get_spirit_name(spirit_id: str | None) -> str:
    if not spirit_id:
        return "—"
    return _load_simple_map("spirits.tsv", "spirit_id", "name").get(
        spirit_id, "Desconocido"
    )


def get_board_name(board_id: str | None) -> str:
    if not board_id:
        return "—"
    return _load_simple_map("boards.tsv", "board_id", "name").get(
        board_id, "Desconocido"
    )


def get_layout_name(layout_id: str | None) -> str:
    if not layout_id:
        return "—"
    return _load_simple_map("layouts.tsv", "layout_id", "name").get(
        layout_id, "Desconocido"
    )


@lru_cache
def get_adversary_catalog() -> dict[str, AdversaryInfo]:
    rows = _load_tsv_rows(
        "adversaries.tsv", ["adversary_id", "name", "level", "difficulty"]
    )
    grouped: dict[str, dict[str, list[AdversaryLevel]]] = {}
    names: dict[str, str] = {}
    for row in rows:
        adversary_id = row["adversary_id"].strip()
        name = row["name"].strip()
        level = row["level"].strip()
        try:
            difficulty = int(row["difficulty"].strip())
        except ValueError:
            continue
        names[adversary_id] = name
        grouped.setdefault(adversary_id, {}).setdefault("levels", []).append(
            AdversaryLevel(level=level, difficulty=difficulty)
        )

    catalog: dict[str, AdversaryInfo] = {}
    for adversary_id, data in grouped.items():
        levels = tuple(data.get("levels", []))
        catalog[adversary_id] = AdversaryInfo(
            adversary_id=adversary_id,
            name=names.get(adversary_id, adversary_id),
            levels=levels,
        )
    return catalog


def get_adversary_name(adversary_id: str | None) -> str:
    if not adversary_id:
        return "—"
    return get_adversary_catalog().get(
        adversary_id,
        AdversaryInfo(
            adversary_id=adversary_id,
            name="Desconocido",
            levels=(),
        ),
    ).name


def get_adversary_levels(adversary_id: str | None) -> tuple[AdversaryLevel, ...]:
    if not adversary_id:
        return ()
    return get_adversary_catalog().get(
        adversary_id,
        AdversaryInfo(adversary_id=adversary_id, name=adversary_id, levels=()),
    ).levels


def get_adversary_difficulty(adversary_id: str | None, level: str | None) -> int | None:
    if not adversary_id or not level:
        return None
    for item in get_adversary_levels(adversary_id):
        if item.level == level:
            return item.difficulty
    return None
