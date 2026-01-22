#!/usr/bin/env python3
"""Generate an Era TSV from input TSVs."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Spirit:
    spirit_id: str


@dataclass(frozen=True)
class Board:
    board_id: str


def require_columns(fieldnames: Sequence[str] | None, required: Iterable[str], path: Path) -> None:
    if fieldnames is None:
        raise ValueError(f"TSV sin cabecera: {path}")
    missing = [name for name in required if name not in fieldnames]
    if missing:
        missing_list = ", ".join(missing)
        raise ValueError(f"Faltan columnas en {path}: {missing_list}")


def load_spirits(path: Path) -> list[Spirit]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        require_columns(reader.fieldnames, ["spirit_id"], path)
        return [Spirit(spirit_id=row["spirit_id"].strip()) for row in reader if row.get("spirit_id")]


def load_boards(path: Path) -> list[Board]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        require_columns(reader.fieldnames, ["board_id"], path)
        return [Board(board_id=row["board_id"].strip()) for row in reader if row.get("board_id")]


def validate_adversaries(path: Path) -> None:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        require_columns(reader.fieldnames, ["adversary_id"], path)


def generate_round_robin(spirits: Sequence[Spirit]) -> list[list[tuple[Spirit, Spirit]]]:
    total = len(spirits)
    if total < 2:
        raise ValueError("Se necesitan al menos 2 espíritus para generar jornadas")
    if total % 2 != 0:
        raise ValueError("El número de espíritus debe ser par para formar parejas")

    order = list(spirits)
    rounds: list[list[tuple[Spirit, Spirit]]] = []

    for _ in range(total - 1):
        pairs: list[tuple[Spirit, Spirit]] = []
        for idx in range(total // 2):
            spirit_1 = order[idx]
            spirit_2 = order[total - 1 - idx]
            pairs.append((spirit_1, spirit_2))
        rounds.append(pairs)

        fixed = order[0]
        remaining = order[1:]
        remaining = [remaining[-1]] + remaining[:-1]
        order = [fixed] + remaining

    return rounds


def assign_boards(boards: Sequence[Board], match_count: int) -> list[tuple[Board, Board]]:
    if len(boards) < 2:
        raise ValueError("Se necesitan al menos 2 tableros para asignar por incursión")
    slots = match_count * 2
    base = slots // len(boards)
    remainder = slots % len(boards)

    sequence: list[Board] = []
    for index, board in enumerate(boards):
        repetitions = base + (1 if index < remainder else 0)
        sequence.extend([board] * repetitions)

    first_half = sequence[:match_count]
    second_half = sequence[match_count:]
    if len(second_half) != match_count:
        raise ValueError("No hay suficientes tableros para completar la jornada")

    for idx in range(match_count):
        if first_half[idx] == second_half[idx]:
            swap_idx = (idx + 1) % len(second_half)
            second_half[idx], second_half[swap_idx] = second_half[swap_idx], second_half[idx]

    return list(zip(first_half, second_half))


def write_era_tsv(
    path: Path,
    era_id: str,
    rounds: Sequence[Sequence[tuple[Spirit, Spirit]]],
    boards: Sequence[Board],
) -> None:
    headers = [
        "era_id",
        "period_index",
        "incursion_index",
        "spirit_1_id",
        "spirit_2_id",
        "board_1",
        "board_2",
        "board_layout",
        "adversary_id",
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(headers)

        for period_index, pairs in enumerate(rounds, start=1):
            board_pairs = assign_boards(boards, len(pairs))
            for incursion_index, ((spirit_1, spirit_2), (board_1, board_2)) in enumerate(
                zip(pairs, board_pairs),
                start=1,
            ):
                writer.writerow(
                    [
                        era_id,
                        period_index,
                        incursion_index,
                        spirit_1.spirit_id,
                        spirit_2.spirit_id,
                        board_1.board_id,
                        board_2.board_id,
                        "",
                        "",
                    ]
                )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genera un TSV de Era desde ficheros TSV de entrada.")
    parser.add_argument("--era-id", required=True, help="Identificador de Era (era_id).")
    parser.add_argument(
        "--spirits",
        type=Path,
        default=Path("pc/data/input/spirits.tsv"),
        help="Ruta al TSV de espíritus.",
    )
    parser.add_argument(
        "--boards",
        type=Path,
        default=Path("pc/data/input/boards.tsv"),
        help="Ruta al TSV de tableros.",
    )
    parser.add_argument(
        "--adversaries",
        type=Path,
        default=Path("pc/data/input/adversaries.tsv"),
        help="Ruta al TSV de adversarios (solo validación de estructura).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("pc/data/output/era.tsv"),
        help="Ruta de salida del TSV de Era.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    spirits = load_spirits(args.spirits)
    boards = load_boards(args.boards)
    validate_adversaries(args.adversaries)

    rounds = generate_round_robin(spirits)
    write_era_tsv(args.output, args.era_id, rounds, boards)


if __name__ == "__main__":
    main()
