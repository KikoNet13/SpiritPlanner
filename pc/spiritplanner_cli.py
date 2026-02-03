#!/usr/bin/env python3
"""Interactive console tool for SpiritPlanner PC workflows."""

from __future__ import annotations

import os
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - dotenv is expected in production
    load_dotenv = None

IS_FROZEN = bool(getattr(sys, "frozen", False))
REPO_ROOT = Path(__file__).resolve().parents[1]
EXECUTABLE_DIR = (
    Path(sys.executable).resolve().parent if IS_FROZEN else REPO_ROOT
)

CATALOG_FILENAMES: dict[str, str] = {
    "spirits": "spirits.tsv",
    "boards": "boards.tsv",
    "adversaries": "adversaries.tsv",
    "layouts": "layouts.tsv",
}
CATALOG_PRIMARY_RELATIVE_DIR = Path("app") / "assets" / "catalogs"
CATALOG_FALLBACK_RELATIVE_DIR = Path("pc") / "data" / "input"


def _build_dotenv_candidates() -> list[Path]:
    candidates: list[Path] = [
        EXECUTABLE_DIR / ".env",
        EXECUTABLE_DIR.parent / ".env",
    ]
    if not IS_FROZEN:
        candidates.append(REPO_ROOT / ".env")

    unique_candidates: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique_candidates.append(resolved)
    return unique_candidates


def _load_runtime_dotenv() -> Path | None:
    if load_dotenv is None:
        return None

    for dotenv_path in _build_dotenv_candidates():
        if not dotenv_path.is_file():
            continue
        load_dotenv(dotenv_path, override=False)
        return dotenv_path
    return None


def _resolve_credentials_path(raw_value: str | None) -> Path | None:
    if not raw_value:
        return None

    expanded = Path(raw_value).expanduser()
    if expanded.is_absolute():
        return expanded

    cwd_candidate = (Path.cwd() / expanded).resolve()
    if cwd_candidate.exists():
        return cwd_candidate

    return (EXECUTABLE_DIR / expanded).resolve()


def _is_debug_enabled() -> bool:
    return os.getenv("SPIRITPLANNER_DEBUG") == "1"


def _configure_runtime_warnings(debug_enabled: bool) -> None:
    if debug_enabled:
        return
    warnings.filterwarnings(
        "ignore",
        category=FutureWarning,
        module="google.api_core._python_version_support",
    )


def _print_runtime_debug(dotenv_loaded: Path | None) -> None:
    credentials_value = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    credentials_path = _resolve_credentials_path(credentials_value)

    print("\n[DEBUG] Diagnostico de entorno")
    print(f"[DEBUG] cwd: {Path.cwd()}")
    print(f"[DEBUG] exe_dir: {EXECUTABLE_DIR}")
    print(
        "[DEBUG] .env cargado: "
        f"{dotenv_loaded if dotenv_loaded is not None else 'ninguno'}"
    )
    print(
        "[DEBUG] GOOGLE_APPLICATION_CREDENTIALS: "
        f"{credentials_value if credentials_value else 'no definido'}"
    )
    if credentials_path is None:
        print("[DEBUG] fichero de credenciales en disco: no (ruta no definida)")
    else:
        print(
            "[DEBUG] fichero de credenciales en disco: "
            f"{'si' if credentials_path.is_file() else 'no'} ({credentials_path})"
        )


def _bootstrap_runtime_environment() -> None:
    dotenv_loaded = _load_runtime_dotenv()
    debug_enabled = _is_debug_enabled()
    _configure_runtime_warnings(debug_enabled)
    if debug_enabled:
        _print_runtime_debug(dotenv_loaded)


def _has_credentials_configured() -> bool:
    value = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    return bool(value)


def _print_missing_credentials_message() -> None:
    print("No se encontraron credenciales (GOOGLE_APPLICATION_CREDENTIALS).")
    print(
        "Coloca un .env junto al .exe (misma carpeta) o configura la "
        "variable de entorno en Windows."
    )


def _ensure_credentials_configured() -> bool:
    if _has_credentials_configured():
        return True
    _print_missing_credentials_message()
    return False


def _catalog_search_dirs(base_dir: Path) -> tuple[Path, Path]:
    primary_dir = (base_dir / CATALOG_PRIMARY_RELATIVE_DIR).resolve()
    fallback_dir = (base_dir / CATALOG_FALLBACK_RELATIVE_DIR).resolve()
    return primary_dir, fallback_dir


def resolve_catalog_paths(base_dir: Path) -> dict[str, Path]:
    primary_dir, fallback_dir = _catalog_search_dirs(base_dir)
    resolved: dict[str, Path] = {}

    for catalog_key, filename in CATALOG_FILENAMES.items():
        primary_path = primary_dir / filename
        fallback_path = fallback_dir / filename
        if primary_path.is_file():
            resolved[catalog_key] = primary_path
            continue
        if fallback_path.is_file():
            resolved[catalog_key] = fallback_path

    return resolved


def _print_catalog_resolution_debug(base_dir: Path, resolved_paths: dict[str, Path]) -> None:
    primary_dir, fallback_dir = _catalog_search_dirs(base_dir)
    print("[DEBUG] Catálogos TSV (resolución):")
    print(f"[DEBUG] ruta primaria: {primary_dir}")
    print(f"[DEBUG] ruta fallback: {fallback_dir}")
    for catalog_key, filename in CATALOG_FILENAMES.items():
        final_path = resolved_paths.get(catalog_key)
        if final_path is None:
            print(f"[DEBUG] - {filename}: no encontrado")
        else:
            print(f"[DEBUG] - {filename}: {final_path}")


def _print_missing_catalogs_message(base_dir: Path, missing_filenames: list[str]) -> None:
    primary_dir, fallback_dir = _catalog_search_dirs(base_dir)
    print("No se encontraron los catálogos TSV necesarios.")
    print(f"Busqué en: {primary_dir} y {fallback_dir}")
    print(f"Faltan: {', '.join(missing_filenames)}")


def _resolve_required_catalog_paths(base_dir: Path) -> dict[str, Path] | None:
    resolved_paths = resolve_catalog_paths(base_dir)
    if _is_debug_enabled():
        _print_catalog_resolution_debug(base_dir, resolved_paths)

    missing_filenames = [
        filename
        for catalog_key, filename in CATALOG_FILENAMES.items()
        if catalog_key not in resolved_paths
    ]
    if missing_filenames:
        _print_missing_catalogs_message(base_dir, missing_filenames)
        return None

    return resolved_paths


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


def _load_list_eras_function() -> Any:
    if __package__:
        from .firestore_service import list_eras
    else:
        from firestore_service import list_eras
    return list_eras


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


def _is_credentials_error(exc: Exception) -> bool:
    error_text = f"{exc.__class__.__name__}: {exc}".lower()
    return (
        "defaultcredentialserror" in error_text
        or "application default credentials" in error_text
        or "could not automatically determine credentials" in error_text
        or "google_application_credentials" in error_text
    )


def _format_operation_error(exc: Exception) -> str:
    error_text = f"{exc.__class__.__name__}: {exc}".lower()

    if _is_credentials_error(exc):
        return (
            "No se encontraron credenciales de Google Cloud (ADC). "
            "Configura GOOGLE_APPLICATION_CREDENTIALS o inicia ADC con gcloud."
        )
    if "no module named 'firebase_admin'" in error_text:
        return "Falta la dependencia 'firebase-admin' en este entorno."
    if str(exc).strip():
        return str(exc).strip()
    return "Error inesperado al operar con Firestore."


def _print_error(prefix: str, exc: Exception) -> None:
    print(f"{prefix}: {_format_operation_error(exc)}")


def _format_timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if value is None:
        return "-"
    return str(value)


def _build_era_row_label(row: dict[str, Any]) -> str:
    era_id = str(row["era_id"])
    updated_at = _format_timestamp(row.get("updated_at"))
    created_at = _format_timestamp(row.get("created_at"))
    return f"{era_id} (updated_at: {updated_at}, created_at: {created_at})"


def select_era_interactively(action_label_es: str) -> Optional[str]:
    if not _ensure_credentials_configured():
        return None

    while True:
        try:
            list_eras = _load_list_eras_function()
            rows: list[dict[str, Any]] = list_eras()
        except Exception as exc:
            _print_error("No se pudo cargar la lista de eras", exc)
            return None

        if not rows:
            print("No hay eras en Firestore.")
            return None

        print(f"\nSelecciona una era para {action_label_es}:")
        for index, row in enumerate(rows, start=1):
            print(f"{index}) {_build_era_row_label(row)}")
        print("0) Cancelar")
        print("R) Refrescar lista")

        option = input("Elige una opcion: ").strip()
        if option.lower() == "r":
            continue
        if option == "0":
            print("Operacion cancelada.")
            return None
        if option.isdigit():
            selected_index = int(option)
            if 1 <= selected_index <= len(rows):
                return str(rows[selected_index - 1]["era_id"])

        print("Opcion invalida. Escribe un numero de la lista, 0 o R.")


def _run_generate_flow() -> None:
    print("\n=== Generar era ===")
    if not _ensure_credentials_configured():
        return

    catalog_paths = _resolve_required_catalog_paths(EXECUTABLE_DIR)
    if catalog_paths is None:
        return

    era_id = _prompt_text("Era ID", default="1")
    seed = _prompt_seed()

    try:
        run_generate_era = _load_generate_function()
        resolved_seed = run_generate_era(
            era_id=era_id,
            seed=seed,
            spirits_path=catalog_paths["spirits"],
            boards_path=catalog_paths["boards"],
            adversaries_path=catalog_paths["adversaries"],
            layouts_path=catalog_paths["layouts"],
            debug_tsv_path=None,
            write_firestore=True,
            write_tsv=False,
            print_generated_seed=False,
        )
    except Exception as exc:
        _print_error(f"Error al generar la era '{era_id}'", exc)
        return

    print(f"Era '{era_id}' generada correctamente.")
    print(f"seed: {resolved_seed}")


def _run_delete_flow() -> None:
    print("\n=== Eliminar era ===")
    if not _ensure_credentials_configured():
        return

    era_id = select_era_interactively("eliminar")
    if era_id is None:
        return

    try:
        counts = _count_era(era_id)
    except Exception as exc:
        _print_error(f"Error al contar la era '{era_id}'", exc)
        return

    _print_counts(era_id, counts)
    if not _confirm_delete(era_id):
        return

    try:
        _delete_era(era_id)
    except Exception as exc:
        print("Error durante el borrado. La era puede haber quedado eliminada de forma parcial.")
        print(f"Detalle: {_format_operation_error(exc)}")
        return

    try:
        remaining = _count_era(era_id)
    except Exception as exc:
        _print_error("La era se borro, pero fallo la verificacion final", exc)
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
    if not _ensure_credentials_configured():
        return

    catalog_paths = _resolve_required_catalog_paths(EXECUTABLE_DIR)
    if catalog_paths is None:
        return

    era_id = select_era_interactively("reiniciar")
    if era_id is None:
        return

    try:
        counts = _count_era(era_id)
    except Exception as exc:
        _print_error(f"Error al contar la era '{era_id}'", exc)
        return

    _print_counts(era_id, counts)
    if not _confirm_delete(era_id):
        return

    seed = _prompt_seed()

    try:
        _delete_era(era_id)
    except Exception as exc:
        print("Error durante el borrado. La era puede haber quedado eliminada de forma parcial.")
        print(f"Detalle: {_format_operation_error(exc)}")
        return

    try:
        run_generate_era = _load_generate_function()
        resolved_seed = run_generate_era(
            era_id=era_id,
            seed=seed,
            spirits_path=catalog_paths["spirits"],
            boards_path=catalog_paths["boards"],
            adversaries_path=catalog_paths["adversaries"],
            layouts_path=catalog_paths["layouts"],
            debug_tsv_path=None,
            write_firestore=True,
            write_tsv=False,
            print_generated_seed=False,
        )
    except Exception as exc:
        print("Error al regenerar la era despues del borrado.")
        print(f"Detalle: {_format_operation_error(exc)}")
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
    _bootstrap_runtime_environment()

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
