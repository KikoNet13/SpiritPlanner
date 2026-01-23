from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from app.utils.logger import get_logger

logger = get_logger(__name__)

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
    data_dir = Path(__file__).resolve().parents[2] / "pc" / "data" / "input"
    logger.debug("Resolved data directory=%s", data_dir)
    return data_dir


def _load_tsv_rows(filename: str, required_fields: Iterable[str]) -> list[dict[str, str]]:
    path = _data_dir() / filename
    logger.debug(
        "Loading TSV rows file=%s required_fields=%s", path, list(required_fields)
    )
    if not path.exists():
        logger.warning("TSV file not found: %s", path)
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames:
            logger.warning("TSV file missing headers: %s", path)
            return []
        if any(field not in reader.fieldnames for field in required_fields):
            logger.warning(
                "TSV file missing required fields. file=%s headers=%s required=%s",
                path,
                reader.fieldnames,
                list(required_fields),
            )
            return []
        rows = [
            row
            for row in reader
            if all(row.get(field) for field in required_fields)
        ]
        logger.debug("Loaded %s rows from %s", len(rows), path)
        return rows


@lru_cache
def _load_simple_map(filename: str, key_field: str, value_field: str) -> dict[str, str]:
    logger.debug(
        "Loading simple map filename=%s key_field=%s value_field=%s",
        filename,
        key_field,
        value_field,
    )
    rows = _load_tsv_rows(filename, [key_field, value_field])
    mapping = {
        row[key_field].strip(): row[value_field].strip()
        for row in rows
        if row.get(key_field) and row.get(value_field)
    }
    logger.debug("Loaded mapping size=%s for filename=%s", len(mapping), filename)
    return mapping


def get_spirit_name(spirit_id: str | None) -> str:
    logger.debug("get_spirit_name spirit_id=%s", spirit_id)
    if not spirit_id:
        return "—"
    name = _load_simple_map("spirits.tsv", "spirit_id", "name").get(
        spirit_id, "Desconocido"
    )
    logger.debug("Resolved spirit name=%s for spirit_id=%s", name, spirit_id)
    return name


def get_board_name(board_id: str | None) -> str:
    logger.debug("get_board_name board_id=%s", board_id)
    if not board_id:
        return "—"
    name = _load_simple_map("boards.tsv", "board_id", "name").get(
        board_id, "Desconocido"
    )
    logger.debug("Resolved board name=%s for board_id=%s", name, board_id)
    return name


def get_layout_name(layout_id: str | None) -> str:
    logger.debug("get_layout_name layout_id=%s", layout_id)
    if not layout_id:
        return "—"
    name = _load_simple_map("layouts.tsv", "layout_id", "name").get(
        layout_id, "Desconocido"
    )
    logger.debug("Resolved layout name=%s for layout_id=%s", name, layout_id)
    return name


@lru_cache
def get_adversary_catalog() -> dict[str, AdversaryInfo]:
    logger.debug("Loading adversary catalog")
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
            logger.warning(
                "Invalid difficulty value for adversary_id=%s value=%s",
                adversary_id,
                row.get("difficulty"),
            )
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
    logger.debug("Adversary catalog loaded count=%s", len(catalog))
    return catalog


def get_adversary_name(adversary_id: str | None) -> str:
    logger.debug("get_adversary_name adversary_id=%s", adversary_id)
    if not adversary_id:
        return "—"
    name = get_adversary_catalog().get(
        adversary_id,
        AdversaryInfo(
            adversary_id=adversary_id,
            name="Desconocido",
            levels=(),
        ),
    ).name
    logger.debug("Resolved adversary name=%s adversary_id=%s", name, adversary_id)
    return name


def get_adversary_levels(adversary_id: str | None) -> tuple[AdversaryLevel, ...]:
    logger.debug("get_adversary_levels adversary_id=%s", adversary_id)
    if not adversary_id:
        return ()
    levels = get_adversary_catalog().get(
        adversary_id,
        AdversaryInfo(adversary_id=adversary_id, name=adversary_id, levels=()),
    ).levels
    logger.debug("Resolved adversary levels count=%s", len(levels))
    return levels


def get_adversary_difficulty(adversary_id: str | None, level: str | None) -> int | None:
    logger.debug(
        "get_adversary_difficulty adversary_id=%s level=%s", adversary_id, level
    )
    if not adversary_id or not level:
        return None
    for item in get_adversary_levels(adversary_id):
        if item.level == level:
            logger.debug(
                "Matched difficulty=%s for adversary_id=%s level=%s",
                item.difficulty,
                adversary_id,
                level,
            )
            return item.difficulty
    logger.warning(
        "No difficulty found for adversary_id=%s level=%s", adversary_id, level
    )
    return None
