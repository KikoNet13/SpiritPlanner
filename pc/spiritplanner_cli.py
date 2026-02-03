#!/usr/bin/env python3
"""CLI for SpiritPlanner PC tooling."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

DEFAULT_SPIRITS_PATH = Path("pc/data/input/spirits.tsv")
DEFAULT_BOARDS_PATH = Path("pc/data/input/boards.tsv")
DEFAULT_ADVERSARIES_PATH = Path("pc/data/input/adversaries.tsv")
DEFAULT_LAYOUTS_PATH = Path("pc/data/input/layouts.tsv")


app = typer.Typer(
    name="spiritplanner",
    help="CLI de herramientas PC para SpiritPlanner.",
    no_args_is_help=True,
)
era_app = typer.Typer(
    help="Comandos para gestionar eras en Firestore.",
    no_args_is_help=True,
)
app.add_typer(era_app, name="era", help="Operaciones de eras.")


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


def _print_era_counts(era_id: str, counts: Any) -> None:
    typer.echo(f"era_id: {era_id}")
    typer.echo(f"doc_era_exists: {'si' if counts.era_exists else 'no'}")
    typer.echo(f"num_periods: {counts.num_periods}")
    typer.echo(f"num_incursions: {counts.num_incursions}")
    typer.echo(f"num_sessions: {counts.num_sessions}")


def _ensure_delete_guards(era_id: str, force: bool, confirm: str | None) -> None:
    if not force:
        typer.secho(
            "Abortado: para borrar debes indicar --force.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=2)

    if confirm is None:
        typer.secho(
            "Abortado: falta --confirm <era_id> para confirmar el borrado.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=2)

    if confirm != era_id:
        typer.secho(
            "Abortado: --confirm debe coincidir exactamente con --era-id.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=2)


def _count_era_or_exit(era_id: str) -> Any:
    try:
        count_era_tree, _ = _load_era_admin_functions()
        return count_era_tree(era_id)
    except Exception as exc:
        typer.secho(
            f"Error al contar la era '{era_id}': {exc}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)


def _delete_era_or_exit(era_id: str) -> None:
    try:
        _, delete_era_tree = _load_era_admin_functions()
        delete_era_tree(era_id)
    except Exception as exc:
        typer.secho(
            "Error durante el borrado. La era puede haber quedado eliminada de forma parcial.",
            fg=typer.colors.RED,
            err=True,
        )
        typer.secho(f"Detalle: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


@era_app.command("generate", help="Genera una era en Firestore desde TSV.")
def era_generate(
    era_id: str = typer.Option(..., "--era-id", help="Identificador de la era."),
    seed: int | None = typer.Option(
        None, "--seed", help="Semilla opcional para resultados reproducibles."
    ),
    spirits: Path = typer.Option(
        DEFAULT_SPIRITS_PATH, "--spirits", help="Ruta al TSV de espiritus."
    ),
    boards: Path = typer.Option(
        DEFAULT_BOARDS_PATH, "--boards", help="Ruta al TSV de tableros."
    ),
    adversaries: Path = typer.Option(
        DEFAULT_ADVERSARIES_PATH, "--adversaries", help="Ruta al TSV de adversarios."
    ),
    layouts: Path = typer.Option(
        DEFAULT_LAYOUTS_PATH, "--layouts", help="Ruta al TSV de layouts."
    ),
    debug_tsv: Path | None = typer.Option(
        None, "--debug-tsv", help="Ruta opcional del TSV de depuracion."
    ),
) -> None:
    try:
        run_generate_era = _load_generate_function()
        resolved_seed = run_generate_era(
            era_id=era_id,
            seed=seed,
            spirits_path=spirits,
            boards_path=boards,
            adversaries_path=adversaries,
            layouts_path=layouts,
            debug_tsv_path=debug_tsv,
            write_firestore=True,
            write_tsv=None,
            print_generated_seed=False,
        )
    except Exception as exc:
        typer.secho(
            f"Error al generar la era '{era_id}': {exc}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    typer.secho(f"Era '{era_id}' generada correctamente.", fg=typer.colors.GREEN)
    typer.echo(f"seed: {resolved_seed}")
    if debug_tsv is not None:
        typer.echo(f"tsv_debug: {debug_tsv}")


@era_app.command("delete", help="Elimina una era completa en cascada.")
def era_delete(
    era_id: str = typer.Option(..., "--era-id", help="Identificador de la era."),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--apply",
        help="Por defecto simula el borrado. Usa --apply para borrar de verdad.",
    ),
    force: bool = typer.Option(
        False, "--force", help="Confirma que el borrado es destructivo."
    ),
    confirm: str | None = typer.Option(
        None, "--confirm", help="Repite el valor de --era-id para confirmar."
    ),
) -> None:
    counts = _count_era_or_exit(era_id)
    _print_era_counts(era_id, counts)

    if dry_run:
        typer.secho(
            "Dry-run completado. No se aplicaron cambios.",
            fg=typer.colors.YELLOW,
        )
        return

    _ensure_delete_guards(era_id, force, confirm)
    _delete_era_or_exit(era_id)

    remaining = _count_era_or_exit(era_id)
    if (
        remaining.era_exists
        or remaining.num_periods
        or remaining.num_incursions
        or remaining.num_sessions
    ):
        typer.secho(
            "Advertencia: quedaron documentos tras el borrado. Revisa el estado manualmente.",
            fg=typer.colors.YELLOW,
            err=True,
        )
        _print_era_counts(era_id, remaining)
        raise typer.Exit(code=1)

    typer.secho(f"Era '{era_id}' eliminada correctamente.", fg=typer.colors.GREEN)


@era_app.command("reset", help="Borra una era y la vuelve a generar.")
def era_reset(
    era_id: str = typer.Option(..., "--era-id", help="Identificador de la era."),
    seed: int | None = typer.Option(
        None, "--seed", help="Semilla opcional para resultados reproducibles."
    ),
    spirits: Path = typer.Option(
        DEFAULT_SPIRITS_PATH, "--spirits", help="Ruta al TSV de espiritus."
    ),
    boards: Path = typer.Option(
        DEFAULT_BOARDS_PATH, "--boards", help="Ruta al TSV de tableros."
    ),
    adversaries: Path = typer.Option(
        DEFAULT_ADVERSARIES_PATH, "--adversaries", help="Ruta al TSV de adversarios."
    ),
    layouts: Path = typer.Option(
        DEFAULT_LAYOUTS_PATH, "--layouts", help="Ruta al TSV de layouts."
    ),
    debug_tsv: Path | None = typer.Option(
        None, "--debug-tsv", help="Ruta opcional del TSV de depuracion."
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--apply",
        help="Por defecto solo simula. Usa --apply para ejecutar reset real.",
    ),
    force: bool = typer.Option(
        False, "--force", help="Confirma que el borrado es destructivo."
    ),
    confirm: str | None = typer.Option(
        None, "--confirm", help="Repite el valor de --era-id para confirmar."
    ),
) -> None:
    counts = _count_era_or_exit(era_id)
    _print_era_counts(era_id, counts)

    if dry_run:
        typer.secho(
            "Dry-run completado. No se aplicaron cambios.",
            fg=typer.colors.YELLOW,
        )
        return

    _ensure_delete_guards(era_id, force, confirm)
    _delete_era_or_exit(era_id)

    try:
        run_generate_era = _load_generate_function()
        resolved_seed = run_generate_era(
            era_id=era_id,
            seed=seed,
            spirits_path=spirits,
            boards_path=boards,
            adversaries_path=adversaries,
            layouts_path=layouts,
            debug_tsv_path=debug_tsv,
            write_firestore=True,
            write_tsv=None,
            print_generated_seed=False,
        )
    except Exception as exc:
        typer.secho(
            "Error al regenerar la era despues del borrado.",
            fg=typer.colors.RED,
            err=True,
        )
        typer.secho(f"Detalle: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    typer.secho(f"Era '{era_id}' reiniciada correctamente.", fg=typer.colors.GREEN)
    typer.echo(f"seed: {resolved_seed}")
    if debug_tsv is not None:
        typer.echo(f"tsv_debug: {debug_tsv}")


if __name__ == "__main__":
    app()
