from __future__ import annotations

import sys
import types
from pathlib import Path


root = Path(__file__).resolve().parent

if "app" not in sys.modules:
    app_mod = types.ModuleType("app")
    app_mod.__path__ = [str(root)]
    sys.modules["app"] = app_mod

from app.main import main as app_main


async def main(page) -> None:
    await app_main(page)


if __name__ == "__main__":
    import flet as ft

    ft.run(main)
