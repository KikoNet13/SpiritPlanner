from __future__ import annotations

import csv
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import flet as ft


ASSETS_DIR = Path(__file__).resolve().parent / "assets"
CALIBRATION_PATH = Path(__file__).resolve().parent / "calibration.json"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PC_LAYOUTS_TSV_PATH = PROJECT_ROOT / "pc" / "data" / "input" / "layouts.tsv"
BOARD_IDS = ["a", "b", "c", "d"]
VIEWPORT_ASPECT_RATIO = 16 / 9
CONTROLS_PANE_WIDTH = 460.0

DEFAULT_BOARD_HEIGHT_PCT = 0.90
DEFAULT_GUIDE_OPACITY_PCT = 70

DX_DY_MIN = -1.0
DX_DY_MAX = 1.0
DX_DY_DECIMALS = 3
DX_DY_DIVISIONS = 2000
ROT_MIN_DEG = -180.0
ROT_MAX_DEG = 180.0

DEFAULT_LEFT_SLOT = {"dx": -0.45, "dy": 0.00, "rot_deg": 0.00}
DEFAULT_RIGHT_SLOT = {"dx": 0.45, "dy": 0.00, "rot_deg": 0.00}

GUIDE_MISSING_TEXT = "No hay imagen guia para este layout"
CENTER_ALIGN = ft.Alignment(0, 0)


@dataclass
class SlotTransform:
    dx: float = 0.0
    dy: float = 0.0
    rot_deg: float = 0.0

    def as_json(self) -> dict[str, float]:
        return {
            "dx": round(self.dx, 6),
            "dy": round(self.dy, 6),
            "rot_deg": round(self.rot_deg, 6),
        }


@dataclass
class SliderInputControl:
    slider: ft.Slider
    input_field: ft.TextField
    min_value: float
    max_value: float
    decimals: int


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _read_png_size(path: Path) -> tuple[int, int]:
    if not path.exists():
        return (1, 1)

    with path.open("rb") as file:
        header = file.read(24)

    png_sig = b"\x89PNG\r\n\x1a\n"
    if len(header) < 24 or header[:8] != png_sig:
        return (1, 1)

    width, height = struct.unpack(">II", header[16:24])
    if width <= 0 or height <= 0:
        return (1, 1)
    return width, height


def _load_layout_ids_from_pc_tsv() -> list[str]:
    if not PC_LAYOUTS_TSV_PATH.exists():
        return []

    layout_ids: list[str] = []
    try:
        with PC_LAYOUTS_TSV_PATH.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            for row in reader:
                layout_id = (row.get("layout_id") or "").strip()
                player_count = (row.get("player_count") or "").strip()
                if not layout_id:
                    continue
                if player_count and player_count != "2":
                    continue
                if layout_id not in layout_ids:
                    layout_ids.append(layout_id)
    except OSError:
        return []

    return layout_ids


def _load_layout_ids_from_calibration_file() -> list[str]:
    try:
        data = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return []

    layouts = data.get("layouts")
    if not isinstance(layouts, dict):
        return []

    return sorted(str(layout_id) for layout_id in layouts.keys())


class BoardLayoutCalibrator:
    def __init__(self, page: ft.Page):
        self.page = page

        self.left_transform = SlotTransform(**DEFAULT_LEFT_SLOT)
        self.right_transform = SlotTransform(**DEFAULT_RIGHT_SLOT)
        self.layout_ids = (
            _load_layout_ids_from_pc_tsv() or _load_layout_ids_from_calibration_file()
        )

        self.board_aspects = self._load_board_aspects()
        self.viewport_width = 960.0
        self.viewport_height = 540.0

        self.layout_dropdown = ft.Dropdown(
            label="Layout",
            value=self.layout_ids[0] if self.layout_ids else None,
            width=200,
            options=[ft.dropdown.Option(layout_id) for layout_id in self.layout_ids],
            disabled=not self.layout_ids,
            dense=True,
            on_select=self._on_layout_change,
        )
        self.left_board_dropdown = ft.Dropdown(
            label="Tablero Left",
            value="a",
            width=190,
            options=[ft.dropdown.Option(board_id) for board_id in BOARD_IDS],
            dense=True,
            on_select=self._on_board_change,
        )
        self.right_board_dropdown = ft.Dropdown(
            label="Tablero Right",
            value="b",
            width=190,
            options=[ft.dropdown.Option(board_id) for board_id in BOARD_IDS],
            dense=True,
            on_select=self._on_board_change,
        )

        self.board_size_slider = ft.Slider(
            min=50,
            max=120,
            divisions=70,
            value=DEFAULT_BOARD_HEIGHT_PCT * 100,
            on_change=self._on_board_size_change,
        )
        self.board_size_value_text = ft.Text("", width=48)

        self.guide_opacity_slider = ft.Slider(
            min=0,
            max=100,
            divisions=100,
            value=DEFAULT_GUIDE_OPACITY_PCT,
            on_change=self._on_guide_opacity_change,
        )
        self.guide_opacity_value_text = ft.Text("", width=48)

        self.grid_checkbox = ft.Checkbox(
            label="Rejilla",
            value=False,
            on_change=self._on_grid_change,
        )

        self.save_button = ft.Button("Guardar", on_click=self._save_calibration)
        self.load_button = ft.OutlinedButton("Cargar", on_click=self._load_calibration)

        self.status_text = ft.Text(value="", size=12)
        self.help_text = ft.Text(
            "Ajusta Left/Right hasta encajar con la guia y pulsa Guardar.",
            size=12,
            color="#334155",
        )
        self.guide_warning_text = ft.Text(
            value=GUIDE_MISSING_TEXT,
            size=12,
            color="#b45309",
            visible=False,
        )

        self.left_values_text = ft.Text(size=12, selectable=True)
        self.right_values_text = ft.Text(size=12, selectable=True)
        self.slot_editor_controls: dict[str, dict[str, SliderInputControl]] = {
            "left": {},
            "right": {},
        }
        self.group_editor_controls: dict[str, SliderInputControl] = {}
        self.group_deltas: dict[str, float] = {"dx": 0.0, "dy": 0.0, "rot_deg": 0.0}
        self._syncing_editor_values = False

        self.viewport_stack = ft.Stack(
            controls=[],
            clip_behavior=ft.ClipBehavior.NONE,
            width=self.viewport_width,
            height=self.viewport_height,
        )
        self.viewport_frame = ft.Container(
            width=self.viewport_width,
            height=self.viewport_height,
            border=ft.Border.all(1, "#cbd5e1"),
            bgcolor="#f8fafc",
            alignment=CENTER_ALIGN,
            content=self.viewport_stack,
        )
        self.viewport_wrapper = ft.Container(
            alignment=CENTER_ALIGN,
            padding=ft.Padding.symmetric(vertical=6),
            content=self.viewport_frame,
        )

        self.left_panel = self._build_slot_panel(
            slot="left", title="Left", readout=self.left_values_text
        )
        self.right_panel = self._build_slot_panel(
            slot="right", title="Right", readout=self.right_values_text
        )
        self.controls_pane_container: ft.Container | None = None

    def mount(self) -> None:
        self.page.title = "Board Layout Calibrator"
        self.page.padding = 10
        self.page.scroll = ft.ScrollMode.HIDDEN
        self.page.on_resize = self._on_page_resize

        selection_section = ft.Container(
            padding=8,
            border=ft.Border.all(1, "#cbd5e1"),
            border_radius=10,
            bgcolor="#f8fafc",
            content=ft.Column(
                controls=[
                    ft.Text("Seleccion", size=14, weight=ft.FontWeight.BOLD),
                    self.layout_dropdown,
                    self.left_board_dropdown,
                    self.right_board_dropdown,
                    self.grid_checkbox,
                    ft.Row(
                        controls=[
                            ft.Text("Tamano del tablero"),
                            ft.Container(content=self.board_size_slider, expand=True),
                            self.board_size_value_text,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("Opacidad guia"),
                            ft.Container(
                                content=self.guide_opacity_slider, expand=True
                            ),
                            self.guide_opacity_value_text,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                ],
                spacing=5,
            ),
        )

        actions_section = ft.Container(
            padding=8,
            border=ft.Border.all(1, "#cbd5e1"),
            border_radius=10,
            bgcolor="#f8fafc",
            content=ft.Column(
                controls=[
                    ft.Text("Acciones", size=14, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        controls=[self.load_button, self.save_button],
                        wrap=True,
                        spacing=8,
                    ),
                    self.status_text,
                ],
                spacing=6,
            ),
        )

        controls_scroll = ft.Column(
            controls=[
                selection_section,
                actions_section,
                self._build_joint_panel(),
                self.left_panel,
                self.right_panel,
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.controls_pane_container = ft.Container(
            width=CONTROLS_PANE_WIDTH,
            border=ft.Border.all(1, "#cbd5e1"),
            border_radius=10,
            bgcolor="#ffffff",
            padding=8,
            content=controls_scroll,
        )

        preview_pane = ft.Container(
            expand=True,
            border=ft.Border.all(1, "#cbd5e1"),
            border_radius=10,
            padding=8,
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=self.viewport_wrapper,
                        expand=True,
                        alignment=CENTER_ALIGN,
                    ),
                    self.guide_warning_text,
                    self.help_text,
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            ),
        )

        self._refresh_preview(update=False)
        self.page.add(
            ft.Row(
                controls=[
                    preview_pane,
                    self.controls_pane_container,
                ],
                spacing=10,
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        )

    def _build_slot_panel(
        self, slot: str, title: str, readout: ft.Text
    ) -> ft.Container:
        return ft.Container(
            padding=8,
            border=ft.Border.all(1, "#cbd5e1"),
            border_radius=10,
            content=ft.Column(
                controls=[
                    ft.Text(f"Slot {title}", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text("Traslacion y rotacion", weight=ft.FontWeight.W_600),
                    self._build_slider_input_row(
                        slot=slot,
                        key="dx",
                        label="X (dx)",
                        min_value=DX_DY_MIN,
                        max_value=DX_DY_MAX,
                        divisions=DX_DY_DIVISIONS,
                        decimals=DX_DY_DECIMALS,
                    ),
                    self._build_slider_input_row(
                        slot=slot,
                        key="dy",
                        label="Y (dy)",
                        min_value=DX_DY_MIN,
                        max_value=DX_DY_MAX,
                        divisions=DX_DY_DIVISIONS,
                        decimals=DX_DY_DECIMALS,
                    ),
                    self._build_slider_input_row(
                        slot=slot,
                        key="rot_deg",
                        label="Rotacion (grados)",
                        min_value=ROT_MIN_DEG,
                        max_value=ROT_MAX_DEG,
                        divisions=360,
                        decimals=0,
                    ),
                    ft.OutlinedButton(
                        "Reset", on_click=lambda _e, s=slot: self._reset_slot(s)
                    ),
                    readout,
                ],
                spacing=5,
            ),
        )

    def _build_joint_panel(self) -> ft.Container:
        return ft.Container(
            padding=8,
            border=ft.Border.all(1, "#cbd5e1"),
            border_radius=10,
            bgcolor="#f8fafc",
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Conjunto (Left+Right)", size=14, weight=ft.FontWeight.BOLD
                    ),
                    self._build_group_slider_input_row(
                        key="dx",
                        label="Delta X (dx)",
                        min_value=DX_DY_MIN,
                        max_value=DX_DY_MAX,
                        divisions=DX_DY_DIVISIONS,
                        decimals=DX_DY_DECIMALS,
                    ),
                    self._build_group_slider_input_row(
                        key="dy",
                        label="Delta Y (dy)",
                        min_value=DX_DY_MIN,
                        max_value=DX_DY_MAX,
                        divisions=DX_DY_DIVISIONS,
                        decimals=DX_DY_DECIMALS,
                    ),
                    self._build_group_slider_input_row(
                        key="rot_deg",
                        label="Delta rotacion (grados)",
                        min_value=ROT_MIN_DEG,
                        max_value=ROT_MAX_DEG,
                        divisions=360,
                        decimals=0,
                    ),
                    ft.Row(
                        controls=[
                            ft.Button("Aplicar", on_click=self._apply_group_deltas),
                            ft.OutlinedButton(
                                "Reset deltas", on_click=self._reset_group_deltas
                            ),
                        ],
                        wrap=True,
                        spacing=8,
                    ),
                ],
                spacing=5,
            ),
        )

    def _make_slider_input_control(
        self,
        *,
        label: str,
        min_value: float,
        max_value: float,
        divisions: int,
        decimals: int,
        on_slider_change: Any,
        on_input_commit: Any,
    ) -> tuple[ft.Column, SliderInputControl]:
        slider = ft.Slider(
            min=min_value,
            max=max_value,
            divisions=divisions,
            on_change=on_slider_change,
        )
        input_field = ft.TextField(
            width=84,
            text_size=12,
            text_align=ft.TextAlign.RIGHT,
            dense=True,
            on_submit=lambda _event: on_input_commit(),
            on_blur=lambda _event: on_input_commit(),
        )
        control = SliderInputControl(
            slider=slider,
            input_field=input_field,
            min_value=min_value,
            max_value=max_value,
            decimals=decimals,
        )
        row = ft.Column(
            controls=[
                ft.Text(label, size=11, color="#334155"),
                ft.Row(
                    controls=[
                        ft.Container(content=slider, expand=True),
                        input_field,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                ),
            ],
            spacing=1,
        )
        return row, control

    def _build_slider_input_row(
        self,
        *,
        slot: str,
        key: str,
        label: str,
        min_value: float,
        max_value: float,
        divisions: int,
        decimals: int,
    ) -> ft.Column:
        row, control = self._make_slider_input_control(
            label=label,
            min_value=min_value,
            max_value=max_value,
            divisions=divisions,
            decimals=decimals,
            on_slider_change=lambda event, s=slot, k=key: self._on_slot_slider_change(
                s, k, event
            ),
            on_input_commit=lambda s=slot, k=key: self._commit_slot_input_value(s, k),
        )
        self.slot_editor_controls[slot][key] = control
        return row

    def _build_group_slider_input_row(
        self,
        *,
        key: str,
        label: str,
        min_value: float,
        max_value: float,
        divisions: int,
        decimals: int,
    ) -> ft.Column:
        row, control = self._make_slider_input_control(
            label=label,
            min_value=min_value,
            max_value=max_value,
            divisions=divisions,
            decimals=decimals,
            on_slider_change=lambda event, k=key: self._on_group_slider_change(
                k, event
            ),
            on_input_commit=lambda k=key: self._commit_group_input_value(k),
        )
        self.group_editor_controls[key] = control
        return row

    def _on_slot_slider_change(
        self, slot: str, key: str, event: ft.ControlEvent
    ) -> None:
        if self._syncing_editor_values:
            return
        raw_value = _safe_float(event.control.value, self._get_slot_value(slot, key))
        self._set_slot_value(slot, key, raw_value)
        self._refresh_preview(update=True)

    def _commit_slot_input_value(self, slot: str, key: str) -> None:
        if self._syncing_editor_values:
            return
        control = self.slot_editor_controls[slot][key]
        parsed = self._read_numeric_text_field(control.input_field.value)
        if parsed is None:
            self._sync_slot_editor_controls(update=True)
            return
        self._set_slot_value(slot, key, parsed)
        self._refresh_preview(update=True)

    def _on_group_slider_change(self, key: str, event: ft.ControlEvent) -> None:
        if self._syncing_editor_values:
            return
        raw_value = _safe_float(event.control.value, self.group_deltas[key])
        self.group_deltas[key] = self._normalize_slot_value(key, raw_value)
        self._sync_group_editor_controls(update=True)

    def _commit_group_input_value(self, key: str) -> None:
        if self._syncing_editor_values:
            return
        control = self.group_editor_controls[key]
        parsed = self._read_numeric_text_field(control.input_field.value)
        if parsed is None:
            self._sync_group_editor_controls(update=True)
            return
        self.group_deltas[key] = self._normalize_slot_value(key, parsed)
        self._sync_group_editor_controls(update=True)

    def _sync_slot_editor_controls(self, update: bool) -> None:
        self._syncing_editor_values = True
        try:
            for slot, slot_controls in self.slot_editor_controls.items():
                for key, control in slot_controls.items():
                    value = self._get_slot_value(slot, key)
                    control.slider.value = value
                    control.input_field.value = self._format_editor_value(
                        value, control.decimals
                    )
                    if update:
                        if control.slider.page is not None:
                            control.slider.update()
                        if control.input_field.page is not None:
                            control.input_field.update()
        finally:
            self._syncing_editor_values = False

    def _sync_group_editor_controls(self, update: bool) -> None:
        self._syncing_editor_values = True
        try:
            for key, control in self.group_editor_controls.items():
                value = self.group_deltas[key]
                control.slider.value = value
                control.input_field.value = self._format_editor_value(
                    value, control.decimals
                )
                if update:
                    if control.slider.page is not None:
                        control.slider.update()
                    if control.input_field.page is not None:
                        control.input_field.update()
        finally:
            self._syncing_editor_values = False

    @staticmethod
    def _read_numeric_text_field(raw_value: Any) -> float | None:
        text = (
            (str(raw_value) if raw_value is not None else "").strip().replace(",", ".")
        )
        if text == "":
            return None
        try:
            return float(text)
        except ValueError:
            return None

    @staticmethod
    def _format_editor_value(value: float, decimals: int) -> str:
        return f"{value:.{decimals}f}"

    def _normalize_slot_value(self, key: str, value: float) -> float:
        if key in ("dx", "dy"):
            clamped = max(DX_DY_MIN, min(DX_DY_MAX, value))
            return round(clamped, DX_DY_DECIMALS)
        if key == "rot_deg":
            clamped = max(ROT_MIN_DEG, min(ROT_MAX_DEG, value))
            return float(round(clamped))
        return value

    def _rotate_point_around_center(
        self,
        x: float,
        y: float,
        center_x: float,
        center_y: float,
        angle_deg: float,
    ) -> tuple[float, float]:
        angle_rad = math.radians(angle_deg)
        cos_value = math.cos(angle_rad)
        sin_value = math.sin(angle_rad)
        rel_x = x - center_x
        rel_y = y - center_y
        rotated_x = center_x + rel_x * cos_value - rel_y * sin_value
        rotated_y = center_y + rel_x * sin_value + rel_y * cos_value
        return rotated_x, rotated_y

    def _apply_group_deltas(self, _event: ft.ControlEvent) -> None:
        delta_dx = self.group_deltas["dx"]
        delta_dy = self.group_deltas["dy"]
        delta_rot = self.group_deltas["rot_deg"]

        left_x = self.left_transform.dx + delta_dx
        left_y = self.left_transform.dy + delta_dy
        right_x = self.right_transform.dx + delta_dx
        right_y = self.right_transform.dy + delta_dy

        center_x = (left_x + right_x) / 2
        center_y = (left_y + right_y) / 2

        left_x, left_y = self._rotate_point_around_center(
            left_x, left_y, center_x, center_y, delta_rot
        )
        right_x, right_y = self._rotate_point_around_center(
            right_x, right_y, center_x, center_y, delta_rot
        )

        self.left_transform.dx = self._normalize_slot_value("dx", left_x)
        self.left_transform.dy = self._normalize_slot_value("dy", left_y)
        self.right_transform.dx = self._normalize_slot_value("dx", right_x)
        self.right_transform.dy = self._normalize_slot_value("dy", right_y)

        self.left_transform.rot_deg = self._normalize_slot_value(
            "rot_deg", self.left_transform.rot_deg + delta_rot
        )
        self.right_transform.rot_deg = self._normalize_slot_value(
            "rot_deg", self.right_transform.rot_deg + delta_rot
        )

        self._reset_group_delta_values()
        self._refresh_preview(update=True)

    def _reset_group_delta_values(self) -> None:
        self.group_deltas["dx"] = 0.0
        self.group_deltas["dy"] = 0.0
        self.group_deltas["rot_deg"] = 0.0

    def _reset_group_deltas(self, _event: ft.ControlEvent) -> None:
        self._reset_group_delta_values()
        self._sync_group_editor_controls(update=True)

    def _get_slot_value(self, slot: str, key: str) -> float:
        transform = self._active_slot_transform(slot)
        return _safe_float(getattr(transform, key, 0.0), 0.0)

    def _set_slot_value(self, slot: str, key: str, value: float) -> None:
        transform = self._active_slot_transform(slot)
        setattr(transform, key, self._normalize_slot_value(key, value))

    @property
    def board_height_pct(self) -> float:
        value = _safe_float(
            self.board_size_slider.value, DEFAULT_BOARD_HEIGHT_PCT * 100
        )
        return value / 100.0

    @property
    def guide_opacity(self) -> float:
        value = _safe_float(self.guide_opacity_slider.value, DEFAULT_GUIDE_OPACITY_PCT)
        return max(0.0, min(1.0, value / 100.0))

    def _load_board_aspects(self) -> dict[str, float]:
        aspects: dict[str, float] = {}
        for board_id in BOARD_IDS:
            width, height = _read_png_size(ASSETS_DIR / "boards" / f"{board_id}.png")
            aspects[board_id] = width / height if height else 1.0
        return aspects

    def _active_slot_transform(self, slot: str) -> SlotTransform:
        return self.left_transform if slot == "left" else self.right_transform

    def _reset_slot(self, slot: str) -> None:
        defaults = DEFAULT_LEFT_SLOT if slot == "left" else DEFAULT_RIGHT_SLOT
        target = self._active_slot_transform(slot)
        target.dx = defaults["dx"]
        target.dy = defaults["dy"]
        target.rot_deg = defaults["rot_deg"]
        self._refresh_preview(update=True)

    def _on_layout_change(self, _event: ft.ControlEvent) -> None:
        self._set_status(
            "Layout cambiado. Pulsa Cargar si quieres traer calibracion guardada."
        )
        self._refresh_preview(update=True)

    def _on_board_change(self, _event: ft.ControlEvent) -> None:
        self._refresh_preview(update=True)

    def _on_board_size_change(self, _event: ft.ControlEvent) -> None:
        self._refresh_preview(update=True)

    def _on_guide_opacity_change(self, _event: ft.ControlEvent) -> None:
        self._refresh_preview(update=True)

    def _on_grid_change(self, _event: ft.ControlEvent) -> None:
        self._refresh_preview(update=True)

    def _on_page_resize(self, _event: ft.ControlEvent) -> None:
        self._refresh_preview(update=True)

    def _refresh_preview(self, update: bool) -> None:
        self._update_scalar_labels()
        self._update_viewport_size()
        self._rebuild_viewport_stack()
        self._update_slot_readouts()
        self._sync_slot_editor_controls(update=update)
        self._sync_group_editor_controls(update=update)
        self._sync_guide_controls()

        if update:
            self.board_size_value_text.update()
            self.guide_opacity_value_text.update()
            self.left_values_text.update()
            self.right_values_text.update()
            self.guide_warning_text.update()
            self.guide_opacity_slider.update()
            self.viewport_frame.update()
            if (
                self.controls_pane_container is not None
                and self.controls_pane_container.page is not None
            ):
                self.controls_pane_container.update()

    def _update_scalar_labels(self) -> None:
        self.board_size_value_text.value = (
            f"{int(round(self.board_size_slider.value or 0))}%"
        )
        self.guide_opacity_value_text.value = (
            f"{int(round(self.guide_opacity_slider.value or 0))}%"
        )

    def _update_slot_readouts(self) -> None:
        self.left_values_text.value = self._format_slot_text(self.left_transform)
        self.right_values_text.value = self._format_slot_text(self.right_transform)

    @staticmethod
    def _format_slot_text(slot: SlotTransform) -> str:
        return f"dx={slot.dx:.3f}  " f"dy={slot.dy:.3f}  " f"rot_deg={slot.rot_deg:.0f}"

    def _update_viewport_size(self) -> None:
        page_width = float(self.page.width or 1200)
        page_height = float(self.page.height or 900)
        controls_width = min(CONTROLS_PANE_WIDTH, max(320.0, page_width * 0.42))
        if self.controls_pane_container is not None:
            self.controls_pane_container.width = controls_width
            self.controls_pane_container.height = max(320.0, page_height - 24.0)

        available_width = max(320.0, page_width - controls_width - 48.0)
        available_height = max(220.0, page_height - 48.0)

        if available_width / available_height > VIEWPORT_ASPECT_RATIO:
            self.viewport_height = available_height
            self.viewport_width = available_height * VIEWPORT_ASPECT_RATIO
        else:
            self.viewport_width = available_width
            self.viewport_height = available_width / VIEWPORT_ASPECT_RATIO

        self.viewport_stack.width = self.viewport_width
        self.viewport_stack.height = self.viewport_height
        self.viewport_frame.width = self.viewport_width
        self.viewport_frame.height = self.viewport_height

    def _rebuild_viewport_stack(self) -> None:
        controls: list[ft.Control] = [
            ft.Container(
                width=self.viewport_width,
                height=self.viewport_height,
                bgcolor="#ffffff",
            )
        ]

        if self._has_guide_image():
            controls.append(
                ft.Image(
                    src=f"layouts/{self.layout_dropdown.value}.png",
                    width=self.viewport_width,
                    height=self.viewport_height,
                    fit=ft.BoxFit.CONTAIN,
                    opacity=self.guide_opacity,
                )
            )
        else:
            controls.append(
                ft.Container(
                    width=self.viewport_width,
                    height=self.viewport_height,
                    alignment=CENTER_ALIGN,
                    content=ft.Text(
                        GUIDE_MISSING_TEXT,
                        size=13,
                        color="#92400e",
                    ),
                )
            )

        controls.append(self._build_board_image("left"))
        controls.append(self._build_board_image("right"))

        if self.grid_checkbox.value:
            controls.extend(self._build_grid_controls())

        self.viewport_stack.controls = controls

    def _build_board_image(self, slot: str) -> ft.Image:
        transform = self._active_slot_transform(slot)
        board_id = (
            self.left_board_dropdown.value
            if slot == "left"
            else self.right_board_dropdown.value
        )
        board_id = board_id if board_id in BOARD_IDS else BOARD_IDS[0]

        board_aspect = self.board_aspects.get(board_id, 1.0)
        board_base_height_px = self.viewport_height * self.board_height_pct

        translate_x_px = transform.dx * board_base_height_px
        translate_y_px = transform.dy * board_base_height_px

        board_height_px = board_base_height_px
        board_width_px = board_height_px * board_aspect

        center_x = (self.viewport_width / 2) + translate_x_px
        center_y = (self.viewport_height / 2) + translate_y_px

        return ft.Image(
            src=f"boards/{board_id}.png",
            fit=ft.BoxFit.CONTAIN,
            width=board_width_px,
            height=board_height_px,
            left=center_x - (board_width_px / 2),
            top=center_y - (board_height_px / 2),
            rotate=ft.Rotate(
                angle=math.radians(transform.rot_deg), alignment=CENTER_ALIGN
            ),
        )

    def _build_grid_controls(self) -> list[ft.Control]:
        width = self.viewport_width
        height = self.viewport_height
        controls: list[ft.Control] = []

        steps = 10
        for index in range(1, steps):
            x = (width / steps) * index
            y = (height / steps) * index
            controls.append(
                ft.Container(left=x, top=0, width=1, height=height, bgcolor="#cbd5e1")
            )
            controls.append(
                ft.Container(left=0, top=y, width=width, height=1, bgcolor="#cbd5e1")
            )

        controls.append(
            ft.Container(
                left=width / 2, top=0, width=2, height=height, bgcolor="#64748b"
            )
        )
        controls.append(
            ft.Container(
                left=0, top=height / 2, width=width, height=2, bgcolor="#64748b"
            )
        )
        return controls

    def _has_guide_image(self) -> bool:
        layout_id = self.layout_dropdown.value or ""
        return (ASSETS_DIR / "layouts" / f"{layout_id}.png").exists()

    def _sync_guide_controls(self) -> None:
        has_guide = self._has_guide_image()
        self.guide_warning_text.visible = not has_guide
        self.guide_opacity_slider.disabled = not has_guide

    def _save_calibration(self, _event: ft.ControlEvent) -> None:
        data = self._read_calibration_file(migrate_legacy=True)
        if data is None:
            return

        layout_id = self.layout_dropdown.value
        if not layout_id:
            self._set_status(
                "No hay layouts disponibles en pc/data/input/layouts.tsv.",
                error=True,
            )
            return

        layouts = data.get("layouts")
        if not isinstance(layouts, dict):
            layouts = {}
            data["layouts"] = layouts

        layouts[layout_id] = {
            "left": self.left_transform.as_json(),
            "right": self.right_transform.as_json(),
        }
        data["schema_version"] = 1

        if not self._write_calibration_file(data):
            return

        self._set_status(f"Guardado: {layout_id} -> {CALIBRATION_PATH.name}")

    def _load_calibration(self, _event: ft.ControlEvent) -> None:
        if not CALIBRATION_PATH.exists():
            self._set_status("No existe calibration.json todavia.", error=True)
            return

        data = self._read_calibration_file(migrate_legacy=True)
        if data is None:
            return

        layouts = data.get("layouts", {})
        if not isinstance(layouts, dict):
            self._set_status("Formato invalido: 'layouts' no es un objeto.", error=True)
            return

        layout_id = self.layout_dropdown.value
        if not layout_id:
            self._set_status(
                "No hay layouts disponibles en pc/data/input/layouts.tsv.",
                error=True,
            )
            return
        layout_data = layouts.get(layout_id)
        if not isinstance(layout_data, dict):
            self._set_status(
                f"No hay calibracion guardada para '{layout_id}'.", error=True
            )
            return

        self.left_transform = self._parse_slot(
            layout_data.get("left"), DEFAULT_LEFT_SLOT
        )
        self.right_transform = self._parse_slot(
            layout_data.get("right"), DEFAULT_RIGHT_SLOT
        )

        self._refresh_preview(update=True)
        self._set_status(f"Cargado: {layout_id}")

    def _read_calibration_file(
        self, migrate_legacy: bool = False
    ) -> dict[str, Any] | None:
        if not CALIBRATION_PATH.exists():
            return {"schema_version": 1, "layouts": {}}

        try:
            with CALIBRATION_PATH.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            self._set_status(f"No se pudo leer calibration.json: {error}", error=True)
            return None

        if not isinstance(data, dict):
            self._set_status(
                "Formato invalido en calibration.json (se esperaba un objeto).",
                error=True,
            )
            return None

        if migrate_legacy and self._migrate_legacy_calibration_data(data):
            self._write_calibration_file(data)

        return data

    def _write_calibration_file(self, data: dict[str, Any]) -> bool:
        try:
            with CALIBRATION_PATH.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, sort_keys=True)
                file.write("\n")
        except OSError as error:
            self._set_status(
                f"No se pudo guardar calibration.json: {error}", error=True
            )
            return False
        return True

    def _migrate_legacy_calibration_data(self, data: dict[str, Any]) -> bool:
        changed = False
        layouts = data.get("layouts")
        if not isinstance(layouts, dict):
            return False

        for layout_data in layouts.values():
            if not isinstance(layout_data, dict):
                continue

            for legacy_ratio_key in ("aspect_ratio", "aspectRatio", "ratio"):
                if legacy_ratio_key in layout_data:
                    del layout_data[legacy_ratio_key]
                    changed = True

            for slot_key in ("left", "right"):
                slot_data = layout_data.get(slot_key)
                if isinstance(slot_data, dict) and "scale" in slot_data:
                    del slot_data["scale"]
                    changed = True

        return changed

    def _parse_slot(self, raw_slot: Any, defaults: dict[str, float]) -> SlotTransform:
        slot = SlotTransform(**defaults)
        if isinstance(raw_slot, dict):
            slot.dx = self._normalize_slot_value(
                "dx", _safe_float(raw_slot.get("dx"), slot.dx)
            )
            slot.dy = self._normalize_slot_value(
                "dy", _safe_float(raw_slot.get("dy"), slot.dy)
            )
            slot.rot_deg = self._normalize_slot_value(
                "rot_deg", _safe_float(raw_slot.get("rot_deg"), slot.rot_deg)
            )
        return slot

    def _set_status(self, message: str, error: bool = False) -> None:
        self.status_text.value = message
        self.status_text.color = "#b91c1c" if error else "#334155"
        if self.status_text.page is not None:
            self.status_text.update()


def main(page: ft.Page) -> None:
    BoardLayoutCalibrator(page).mount()


ft.run(main, assets_dir=str(ASSETS_DIR))
