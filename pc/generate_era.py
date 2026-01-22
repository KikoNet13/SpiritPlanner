#!/usr/bin/env python3
"""Generate an Era TSV from input TSVs."""

from __future__ import annotations

import argparse
import csv
import random
from dataclasses import dataclass
from itertools import cycle
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Spirit:
    spirit_id: str


@dataclass(frozen=True)
class Board:
    board_id: str


@dataclass(frozen=True)
class Layout:
    layout_id: str
    player_count: int
    is_active: int


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


def load_layouts(path: Path) -> list[Layout]:
    layouts: list[Layout] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for row in reader:
            if len(row) < 4:
                continue
            try:
                player_count = int(row[2])
                is_active = int(row[3])
            except ValueError:
                continue
            layouts.append(
                Layout(
                    layout_id=row[0].strip(),
                    player_count=player_count,
                    is_active=is_active,
                )
            )
    return layouts


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


def assign_boards(
    boards: Sequence[Board],
    match_count: int,
    period_index: int,
) -> list[tuple[Board, Board]]:
    if len(boards) < 2:
        raise ValueError("Se necesitan al menos 2 tableros para asignar por incursión")
    slots = match_count * 2
    if slots < len(boards):
        raise ValueError("No hay suficientes incursiones para usar todos los tableros en el periodo")
    if slots % len(boards) != 0:
        raise ValueError("Los tableros no pueden balancearse perfectamente en el periodo")

    shift = (period_index - 1) % len(boards)
    permutation = list(boards[shift:]) + list(boards[:shift])
    repetitions = slots // len(boards)
    sequence = permutation * repetitions

    pairs: list[tuple[Board, Board]] = []
    for idx in range(0, slots, 2):
        pairs.append((sequence[idx], sequence[idx + 1]))

    return pairs


def select_layouts(layouts: Sequence[Layout]) -> list[Layout]:
    filtered = [layout for layout in layouts if layout.player_count == 2 and layout.is_active == 1]
    if not filtered:
        raise ValueError("No hay layouts activos para 2 jugadores")
    return filtered


def assign_layouts(
    layouts: Sequence[Layout],
    match_count: int,
    period_index: int,
) -> list[Layout]:
    if match_count <= 0:
        return []
    shift = (period_index - 1) % len(layouts)
    permutation = list(layouts[shift:]) + list(layouts[:shift])
    if match_count <= len(layouts):
        return permutation[:match_count]
    selection: list[Layout] = []
    for layout in cycle(permutation):
        selection.append(layout)
        if len(selection) >= match_count:
            break
    return selection


def write_era_tsv(
    path: Path,
    era_id: str,
    rounds: Sequence[Sequence[tuple[Spirit, Spirit]]],
    boards: Sequence[Board],
    layouts: Sequence[Layout],
    rng: random.Random,
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
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(headers)

        shuffled_rounds = list(rounds)
        rng.shuffle(shuffled_rounds)

        for period_index, pairs in enumerate(shuffled_rounds, start=1):
            board_pairs = assign_boards(boards, len(pairs), period_index)
            period_layouts = assign_layouts(layouts, len(pairs), period_index)
            rng.shuffle(period_layouts)

            incursion_entries = list(zip(pairs, board_pairs))
            rng.shuffle(incursion_entries)

            for incursion_index, (((spirit_1, spirit_2), (board_1, board_2)), layout) in enumerate(
                zip(incursion_entries, period_layouts),
                start=1,
            ):
                if rng.random() < 0.5:
                    spirit_1, spirit_2 = spirit_2, spirit_1
                if rng.random() < 0.5:
                    board_1, board_2 = board_2, board_1
                writer.writerow(
                    [
                        era_id,
                        period_index,
                        incursion_index,
                        spirit_1.spirit_id,
                        spirit_2.spirit_id,
                        board_1.board_id,
                        board_2.board_id,
                        layout.layout_id,
                    ]
                )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genera un TSV de Era desde ficheros TSV de entrada.")
    parser.add_argument("--era-id", required=True, help="Identificador de Era (era_id).")
    parser.add_argument("--seed", type=int, help="Seed opcional para randomización reproducible.")
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
        "--layouts",
        type=Path,
        default=Path("pc/data/input/layouts.tsv"),
        help="Ruta al TSV de layouts.",
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
    if args.seed is None:
        seed = random.SystemRandom().randint(0, 2**32 - 1)
        print(seed)
    else:
        seed = args.seed
    rng = random.Random(seed)

    spirits = load_spirits(args.spirits)
    boards = load_boards(args.boards)
    validate_adversaries(args.adversaries)
    layouts = select_layouts(load_layouts(args.layouts))

    rounds = generate_round_robin(spirits)
    write_era_tsv(args.output, args.era_id, rounds, boards, layouts, rng)


if __name__ == "__main__":
    main()
