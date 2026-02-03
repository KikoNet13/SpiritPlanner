#!/usr/bin/env python3
"""Interactive console tool for SpiritPlanner PC workflows."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

DEFAULT_SPIRITS_PATH = Path("pc/data/input/spirits.tsv")
DEFAULT_BOARDS_PATH = Path("pc/data/input/boards.tsv")
DEFAULT_ADVERSARIES_PATH = Path("pc/data/input/adversaries.tsv")
DEFAULT_LAYOUTS_PATH = Path("pc/data/input/layouts.tsv")


def _load_era_admin_functions() -> tuple[Any, Any]:
    if __package__:
        from .era_admin import count_era_tree, delete_era_tree
    else:
        from era_admin import count_era_tree, delete_era_tree
    return count_era_tree, delete_era_tree


def _load_generate_function() -> Any:
    if __package__:
        from .generate_era import run_generate_era
    else:
        from generate_era import run_generate_era
    return run_generate_era


def _print_help() -> None:
    print("Uso: spiritplanner [--help]")
    print()
    print("Herramienta PC de SpiritPlanner en modo interactivo.")
    print("Ejecucion normal (menu numerico):")
    print("- python -m pc.spiritplanner_cli")
    print()
    print("Opciones:")
    print("- -h, --help    Muestra esta ayuda breve y termina.")


def _print_counts(era_id: str, counts: Any) -> None:
    print("\nResumen (dry-run):")
    print(f"- era_id: {era_id}")
    print(f"- doc_era_exists: {'si' if counts.era_exists else 'no'}")
    print(f"- num_periods: {counts.num_periods}")
    print(f"- num_incursions: {counts.num_incursions}")
    print(f"- num_sessions: {counts.num_sessions}")


def _count_era(era_id: str) -> Any:
    count_era_tree, _ = _load_era_admin_functions()
    return count_era_tree(era_id)


def _delete_era(era_id: str) -> None:
    _, delete_era_tree = _load_era_admin_functions()
    delete_era_tree(era_id)


def _prompt_text(prompt: str, *, default: str | None = None, required: bool = False) -> str:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        value = input(f"{prompt}{suffix}: ").strip()
        if value:
            return value
        if default is not None:
            return default
        if not required:
            return ""
        print("Entrada invalida: este campo es obligatorio.")


def _prompt_seed() -> int | None:
    while True:
        value = input("Seed (opcional, Enter para aleatorio): ").strip()
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            print("Seed invalida: debe ser un numero entero.")


def _confirm_delete(era_id: str) -> bool:
    confirmation = input(
        f"Escribe exactamente '{era_id}' para confirmar: "
    ).strip()
    if confirmation != era_id:
        print("Abortado: la confirmacion no coincide con el era_id.")
        return False
    return True


def _run_generate_flow() -> None:
    print("\n=== Generar era ===")
    era_id = _prompt_text("Era ID", default="1")
    seed = _prompt_seed()

    try:
        run_generate_era = _load_generate_function()
        resolved_seed = run_generate_era(
            era_id=era_id,
            seed=seed,
            spirits_path=DEFAULT_SPIRITS_PATH,
            boards_path=DEFAULT_BOARDS_PATH,
            adversaries_path=DEFAULT_ADVERSARIES_PATH,
            layouts_path=DEFAULT_LAYOUTS_PATH,
            debug_tsv_path=None,
            write_firestore=True,
            write_tsv=False,
            print_generated_seed=False,
        )
    except Exception as exc:
        print(f"Error al generar la era '{era_id}': {exc}")
        return

    print(f"Era '{era_id}' generada correctamente.")
    print(f"seed: {resolved_seed}")


def _run_delete_flow() -> None:
    print("\n=== Eliminar era ===")
    era_id = _prompt_text("Era ID", required=True)

    try:
        counts = _count_era(era_id)
    except Exception as exc:
        print(f"Error al contar la era '{era_id}': {exc}")
        return

    _print_counts(era_id, counts)
    if not _confirm_delete(era_id):
        return

    try:
        _delete_era(era_id)
    except Exception as exc:
        print("Error durante el borrado. La era puede haber quedado eliminada de forma parcial.")
        print(f"Detalle: {exc}")
        return

    try:
        remaining = _count_era(era_id)
    except Exception as exc:
        print(f"La era se borro, pero fallo la verificacion final: {exc}")
        return

    if (
        remaining.era_exists
        or remaining.num_periods
        or remaining.num_incursions
        or remaining.num_sessions
    ):
        print("Advertencia: quedaron documentos tras el borrado. Revisa el estado manualmente.")
        _print_counts(era_id, remaining)
        return

    print(f"Era '{era_id}' eliminada correctamente.")


def _run_reset_flow() -> None:
    print("\n=== Reiniciar era ===")
    era_id = _prompt_text("Era ID", required=True)

    try:
        counts = _count_era(era_id)
    except Exception as exc:
        print(f"Error al contar la era '{era_id}': {exc}")
        return

    _print_counts(era_id, counts)
    if not _confirm_delete(era_id):
        return

    seed = _prompt_seed()

    try:
        _delete_era(era_id)
    except Exception as exc:
        print("Error durante el borrado. La era puede haber quedado eliminada de forma parcial.")
        print(f"Detalle: {exc}")
        return

    try:
        run_generate_era = _load_generate_function()
        resolved_seed = run_generate_era(
            era_id=era_id,
            seed=seed,
            spirits_path=DEFAULT_SPIRITS_PATH,
            boards_path=DEFAULT_BOARDS_PATH,
            adversaries_path=DEFAULT_ADVERSARIES_PATH,
            layouts_path=DEFAULT_LAYOUTS_PATH,
            debug_tsv_path=None,
            write_firestore=True,
            write_tsv=False,
            print_generated_seed=False,
        )
    except Exception as exc:
        print("Error al regenerar la era despues del borrado.")
        print(f"Detalle: {exc}")
        return

    print(f"Era '{era_id}' reiniciada correctamente.")
    print(f"seed: {resolved_seed}")


def _pause_continue() -> None:
    input("\nPulsa Enter para continuar...")


def _pause_exit() -> None:
    input("\nPulsa Enter para salir...")


def _show_menu() -> None:
    print("\n========================================")
    print("SpiritPlanner - Herramienta PC")
    print("========================================")
    print("1) Generar era")
    print("2) Eliminar era (con recuento previo)")
    print("3) Reiniciar era (eliminar + generar)")
    print("0) Salir")


def _run_interactive_menu() -> None:
    while True:
        _show_menu()
        option = input("Elige una opcion por numero: ").strip()

        if option == "1":
            _run_generate_flow()
            _pause_continue()
            continue

        if option == "2":
            _run_delete_flow()
            _pause_continue()
            continue

        if option == "3":
            _run_reset_flow()
            _pause_continue()
            continue

        if option == "0":
            print("Saliendo de SpiritPlanner.")
            return

        print("Opcion invalida. Elige un numero del menu.")
        _pause_continue()


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    interactive_mode = len(args) == 0

    try:
        if interactive_mode:
            _run_interactive_menu()
        else:
            if len(args) == 1 and args[0] in ("-h", "--help"):
                _print_help()
                return 0
            print("Error: argumentos no soportados.")
            print("Usa --help para ver la ayuda.")
            return 2
        return 0
    except KeyboardInterrupt:
        print("\nOperacion cancelada por el usuario.")
        return 130
    finally:
        if interactive_mode:
            _pause_exit()


if __name__ == "__main__":
    raise SystemExit(main())
