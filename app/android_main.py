from __future__ import annotations

import inspect
import sys
from pathlib import Path


def _find_flat_root() -> Path:
    """
    Locate the directory that contains the flattened app code:
    - main.py
    - screens/
    - services/
    - utils/
    This should work both in dev (repo/app/...) and in APK (zip root).
    """
    start = Path(__file__).resolve().parent

    candidates = [
        start,
        start.parent,
        start / "app",
        start.parent / "app",
    ]

    for p in candidates:
        if (p / "main.py").is_file() and (p / "screens").is_dir():
            return p

    # Fallback: use current directory
    return start


def _ensure_root_on_syspath(root: Path) -> None:
    """Ensure `import main`, `import screens`, etc. resolve against `root`."""
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


ROOT = _find_flat_root()
_ensure_root_on_syspath(ROOT)

# Now `main` resolves to ROOT/main.py and `screens` to ROOT/screens/
from main import main as app_main  # noqa: E402


async def main(page) -> None:
    result = app_main(page)
    if inspect.isawaitable(result):
        await result


if __name__ == "__main__":
    import flet as ft

    ft.run(main)
