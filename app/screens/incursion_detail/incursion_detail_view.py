from __future__ import annotations

import asyncio
import json
import math
import struct
from datetime import datetime, timezone
from pathlib import Path

import flet as ft

from app.screens.incursion_detail.incursion_detail_model import (
    IncursionDetailModel,
    SESSION_STATE_FINALIZED,
    compute_total_seconds,
    get_result_label,
)
from app.screens.incursion_detail.incursion_detail_viewmodel import (
    IncursionDetailViewModel,
)
from app.services.service_registry import get_firestore_service
from app.utils.datetime_format import format_datetime_local
from app.utils.logger import get_logger
from app.utils.router import register_route_loader

logger = get_logger(__name__)


ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
LAYOUTS_DIR = ASSETS_DIR / "layouts"
CALIBRATION_PATH = LAYOUTS_DIR / "calibration.json"
BOARDS_DIR = ASSETS_DIR / "boards"
DEFAULT_BOARD_HEIGHT_PCT = 0.90
CENTER_ALIGN = ft.Alignment(0, 0)
PREVIEW_TEXT_COLOR = ft.Colors.BLUE_GREY_100
PREVIEW_BG_COLOR = ft.Colors.BLUE_GREY_700
CONTENT_SECTION_PADDING = 16.0
DARK_SECTION_PADDING = 20.0
LAYOUT_PLACEHOLDER_WIDTH = 240.0
LAYOUT_PLACEHOLDER_HEIGHT = 140.0
LAYOUT_PLACEHOLDER_MAX_WIDTH = 960.0

_CALIBRATION_CACHE: dict[str, dict[str, dict[str, float]]] | None = None
_BOARD_ASPECT_CACHE: dict[str, float] = {}
_LAYOUT_ASPECT_CACHE: dict[str, float] = {}


def _safe_float(value: object, default: float) -> float:
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


def _load_layout_calibration() -> dict[str, dict[str, dict[str, float]]]:
    global _CALIBRATION_CACHE
    if _CALIBRATION_CACHE is not None:
        return _CALIBRATION_CACHE

    try:
        data = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        _CALIBRATION_CACHE = {}
        return _CALIBRATION_CACHE

    layouts = data.get("layouts")
    if not isinstance(layouts, dict):
        layouts = {}
    _CALIBRATION_CACHE = layouts
    return layouts


def _get_board_aspect(board_id: str) -> float | None:
    if board_id in _BOARD_ASPECT_CACHE:
        return _BOARD_ASPECT_CACHE[board_id]

    board_path = BOARDS_DIR / f"{board_id}.png"
    if not board_path.exists():
        return None

    width, height = _read_png_size(board_path)
    aspect = width / height if height else 1.0
    _BOARD_ASPECT_CACHE[board_id] = aspect
    return aspect


def _get_layout_aspect(layout_id: str) -> float:
    if layout_id in _LAYOUT_ASPECT_CACHE:
        return _LAYOUT_ASPECT_CACHE[layout_id]

    layout_path = LAYOUTS_DIR / f"{layout_id}.png"
    if not layout_path.exists():
        return LAYOUT_PLACEHOLDER_WIDTH / LAYOUT_PLACEHOLDER_HEIGHT

    width, height = _read_png_size(layout_path)
    aspect = width / height if height else LAYOUT_PLACEHOLDER_WIDTH / LAYOUT_PLACEHOLDER_HEIGHT
    _LAYOUT_ASPECT_CACHE[layout_id] = aspect
    return aspect


def _compute_layout_preview_size(
    page_width: float,
    layout_aspect: float,
) -> tuple[float, float]:
    available_width = max(
        0.0,
        page_width - ((CONTENT_SECTION_PADDING + DARK_SECTION_PADDING) * 2.0),
    )
    preview_width = min(LAYOUT_PLACEHOLDER_MAX_WIDTH, available_width)
    preview_height = preview_width / layout_aspect if layout_aspect else 0.0
    return preview_width, preview_height


def _apply_board_layout(
    board_control: ft.Image,
    board_aspect: float,
    slot_data: dict[str, object],
    preview_width: float,
    preview_height: float,
) -> None:
    transform = {
        "dx": _safe_float(slot_data.get("dx"), 0.0),
        "dy": _safe_float(slot_data.get("dy"), 0.0),
        "rot_deg": _safe_float(slot_data.get("rot_deg"), 0.0),
    }

    board_base_height_px = preview_height * DEFAULT_BOARD_HEIGHT_PCT
    translate_x_px = transform["dx"] * board_base_height_px
    translate_y_px = transform["dy"] * board_base_height_px
    board_height_px = board_base_height_px
    board_width_px = board_height_px * board_aspect

    center_x = (preview_width / 2) + translate_x_px
    center_y = (preview_height / 2) + translate_y_px

    board_control.width = board_width_px
    board_control.height = board_height_px
    board_control.left = center_x - (board_width_px / 2)
    board_control.top = center_y - (board_height_px / 2)


@ft.component
def layout_preview(detail: IncursionDetailModel) -> ft.Control:
    page = ft.context.page
    frame_ref = ft.use_ref(None)
    stack_ref = ft.use_ref(None)
    board_controls_ref: ft.Ref[list[tuple[ft.Image, float, dict[str, object]]]] = (
        ft.use_ref([])
    )
    page_width = float(page.width or 900.0)
    layout_aspect = (
        _get_layout_aspect(detail.layout_id)
        if detail.layout_id
        else LAYOUT_PLACEHOLDER_WIDTH / LAYOUT_PLACEHOLDER_HEIGHT
    )
    preview_width, preview_height = _compute_layout_preview_size(
        page_width,
        layout_aspect,
    )

    def build_fallback(message: str) -> ft.Container:
        board_controls_ref.current = []
        stack_ref.current = None
        return ft.Container(
            ref=frame_ref,
            width=preview_width,
            height=preview_height,
            bgcolor=PREVIEW_BG_COLOR,
            border_radius=12,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            alignment=ft.Alignment.CENTER,
            content=ft.Text(
                message,
                color=PREVIEW_TEXT_COLOR,
                size=12,
            ),
        )

    if not detail.layout_id or not detail.board_1_id or not detail.board_2_id:
        preview_frame = build_fallback("Preview no disponible")
        board_controls_data: list[tuple[ft.Image, float, dict[str, object]]] = []
    else:
        calibration = _load_layout_calibration()
        layout_data = calibration.get(detail.layout_id)
        if not isinstance(layout_data, dict):
            preview_frame = build_fallback("Preview no disponible")
            board_controls_data = []
        else:
            left_slot = layout_data.get("left")
            right_slot = layout_data.get("right")
            if not isinstance(left_slot, dict) or not isinstance(right_slot, dict):
                preview_frame = build_fallback("Preview no disponible")
                board_controls_data = []
            else:
                left_aspect = _get_board_aspect(detail.board_1_id)
                right_aspect = _get_board_aspect(detail.board_2_id)
                if left_aspect is None or right_aspect is None:
                    preview_frame = build_fallback("Preview no disponible")
                    board_controls_data = []
                else:
                    board_controls_data = []

                    def build_board_control(
                        board_id: str,
                        board_aspect: float,
                        slot_data: dict[str, object],
                    ) -> ft.Image:
                        transform = {
                            "dx": _safe_float(slot_data.get("dx"), 0.0),
                            "dy": _safe_float(slot_data.get("dy"), 0.0),
                            "rot_deg": _safe_float(slot_data.get("rot_deg"), 0.0),
                        }

                        board_control = ft.Image(
                            src=f"boards/{board_id}.png",
                            fit=ft.BoxFit.CONTAIN,
                            rotate=ft.Rotate(
                                angle=math.radians(transform["rot_deg"]),
                                alignment=CENTER_ALIGN,
                            ),
                        )
                        board_controls_data.append(
                            (board_control, board_aspect, slot_data)
                        )
                        _apply_board_layout(
                            board_control,
                            board_aspect,
                            slot_data,
                            preview_width,
                            preview_height,
                        )
                        return board_control

                    preview_stack = ft.Stack(
                        ref=stack_ref,
                        width=preview_width,
                        height=preview_height,
                        controls=[
                            build_board_control(
                                detail.board_1_id, left_aspect, left_slot
                            ),
                            build_board_control(
                                detail.board_2_id, right_aspect, right_slot
                            ),
                        ],
                    )

                    preview_frame = ft.Container(
                        ref=frame_ref,
                        width=preview_width,
                        height=preview_height,
                        bgcolor=PREVIEW_BG_COLOR,
                        border_radius=12,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        alignment=ft.Alignment.CENTER,
                        content=preview_stack,
                    )

    board_controls_ref.current = board_controls_data

    def apply_preview_size(target_width: float, target_height: float) -> None:
        frame = frame_ref.current
        if not frame:
            return
        frame.width = target_width
        frame.height = target_height
        if preview_stack := stack_ref.current:
            preview_stack.width = target_width
            preview_stack.height = target_height
        for board_control, board_aspect, slot_data in board_controls_ref.current:
            _apply_board_layout(
                board_control,
                board_aspect,
                slot_data,
                target_width,
                target_height,
            )
        frame.update()

    def register_resize_handler():
        def on_resize(_: ft.ControlEvent) -> None:
            updated_width, updated_height = _compute_layout_preview_size(
                float(page.width or 900.0),
                layout_aspect,
            )
            apply_preview_size(updated_width, updated_height)

        page.on_resize = on_resize
        updated_width, updated_height = _compute_layout_preview_size(
            float(page.width or 900.0),
            layout_aspect,
        )
        apply_preview_size(updated_width, updated_height)

        def cleanup() -> None:
            if page.on_resize == on_resize:
                page.on_resize = None

        return cleanup

    ft.use_effect(register_resize_handler, [])

    return preview_frame


def _dark_section(content: ft.Control) -> ft.Container:
    return ft.Container(
        content=content,
        padding=20,
        border_radius=20,
        bgcolor=ft.Colors.BLUE_GREY_900,
    )


def _light_section(content: ft.Control) -> ft.Container:
    return ft.Container(
        content=content,
        padding=16,
        border_radius=16,
        border=ft.Border.all(1, ft.Colors.GREY_300),
        bgcolor=ft.Colors.WHITE,
    )


def _format_total_time(total_seconds: int) -> str:
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


def _format_short_datetime(value: datetime | str | None) -> str:
    display = format_datetime_local(value)
    if display == "—":
        return display
    parts = display.split(" ")
    if len(parts) >= 2:
        date_part = parts[0]
        time_part = parts[1]
        short_date = date_part[:8]
        return f"{short_date} · {time_part}"
    return display


def _split_date_time(dt: datetime | str | None) -> tuple[str, str]:
    display = _format_short_datetime(dt)
    if "·" in display:
        date_part, time_part = [p.strip() for p in display.split("·", 1)]
    else:
        date_part, time_part = display, ""
    return date_part[:8], time_part


@ft.component
def incursion_detail_view(
    era_id: str,
    period_id: str,
    incursion_id: str,
) -> ft.Control:
    logger.debug(
        "Rendering incursion_detail_view era_id=%s period_id=%s incursion_id=%s",
        era_id,
        period_id,
        incursion_id,
    )
    page = ft.context.page
    service = get_firestore_service(page.session)
    view_model, _ = ft.use_state(IncursionDetailViewModel())
    dialog_ref = ft.use_ref(None)

    def load() -> None:
        view_model.ensure_loaded(service, era_id, period_id, incursion_id)

    ft.use_effect(load, [era_id, period_id, incursion_id])

    def register_loader() -> None:
        def loader(params: dict[str, str]) -> None:
            resolved_era_id = params.get("era_id", era_id)
            resolved_period_id = params.get("period_id", period_id)
            resolved_incursion_id = params.get("incursion_id", incursion_id)
            view_model.ensure_loaded(
                service,
                resolved_era_id,
                resolved_period_id,
                resolved_incursion_id,
            )

        register_route_loader(
            page,
            "/eras/{era_id}/periods/{period_id}/incursions/{incursion_id}",
            loader,
        )

    ft.use_effect(register_loader, [era_id, period_id, incursion_id])

    def show_toast() -> None:
        if not view_model.toast_message:
            return
        page.show_dialog(ft.SnackBar(ft.Text(view_model.toast_message)))
        view_model.consume_toast()

    ft.use_effect(show_toast, [view_model.toast_version])

    def score_dialog_effect() -> None:
        if view_model.score_dialog_open and view_model.detail:
            detail = view_model.detail
            result_label = get_result_label(detail.result)
            difficulty_value = detail.difficulty or 0
            formula, _ = view_model.score_preview()
            dialog = dialog_ref.current or ft.AlertDialog(modal=True)
            dialog.title = ft.Text("Detalle de puntuación")
            dialog.content = ft.Column(
                [
                    ft.Text(f"Resultado: {result_label}"),
                    ft.Text(f"Dificultad: {difficulty_value}"),
                    ft.Text(f"Dahan vivos: {detail.dahan_alive}"),
                    ft.Text(f"Plaga en la isla: {detail.blight_on_island}"),
                    ft.Text(f"Fórmula: {formula}"),
                    ft.Text(
                        f"Puntuación: {detail.score}",
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
                tight=True,
            )
            dialog.actions = [
                ft.TextButton(
                    "Cerrar",
                    on_click=lambda _: view_model.close_score_dialog(),
                )
            ]
            if dialog_ref.current is None:
                dialog_ref.current = dialog
                page.show_dialog(dialog)
            else:
                dialog.update()
            return
        if not view_model.score_dialog_open and dialog_ref.current:
            page.pop_dialog()
            dialog_ref.current = None

    ft.use_effect(score_dialog_effect, [view_model.score_dialog_version])

    def timer_effect():
        if not view_model.timer_running:
            return None

        cancelled = False

        async def tick() -> None:
            while view_model.timer_running and not cancelled:
                view_model.tick_timer()
                await asyncio.sleep(1)

        task = (
            page.run_task(tick)
            if hasattr(page, "run_task")
            else asyncio.create_task(tick())
        )

        def cleanup() -> None:
            nonlocal cancelled
            cancelled = True
            if not task.done():
                task.cancel()

        return cleanup

    ft.use_effect(timer_effect, [view_model.timer_running])

    if view_model.loading and not view_model.detail:
        content = ft.Container(
            content=ft.ProgressRing(),
            expand=True,
            alignment=ft.Alignment.CENTER,
        )
    elif view_model.error == "not_found":
        content = ft.Container(
            content=ft.Text("Incursión no encontrada."),
            expand=True,
            alignment=ft.Alignment.CENTER,
        )
    elif not view_model.detail:
        content = ft.Container(
            content=ft.Text("No se pudo cargar la incursión."),
            expand=True,
            alignment=ft.Alignment.CENTER,
        )
    else:
        detail = view_model.detail
        can_edit_level = (
            view_model.session_state != SESSION_STATE_FINALIZED
            and not view_model.has_sessions
        )
        level_options = [
            ft.dropdown.Option(level, f"Nivel {level}")
            for level in view_model.available_adversary_levels()
        ]
        difficulty_value = detail.difficulty
        adversary_level_block: ft.Control
        if can_edit_level:
            adversary_level_block = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            detail.adversary_name,
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_GREY_900,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Dropdown(
                            text_style=ft.TextStyle(
                                size=14, color=ft.Colors.BLUE_GREY_900
                            ),
                            bgcolor=ft.Colors.WHITE,
                            options=level_options,
                            disabled=not bool(level_options),
                            width=220,
                            value=view_model.adversary_level,
                            on_select=lambda event: view_model.update_adversary_level(
                                service, event.control.value
                            ),
                        ),
                        ft.Text(
                            (
                                f"Dificultad: {difficulty_value}"
                                if difficulty_value is not None
                                and view_model.adversary_level
                                else "Dificultad: —"
                            ),
                            size=14,
                            color=ft.Colors.BLUE_GREY_900,
                        ),
                    ],
                    spacing=6,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                bgcolor=ft.Colors.BLUE_GREY_50,
                border_radius=8,
                alignment=ft.Alignment.CENTER,
            )
        else:
            level_display = detail.adversary_level or "—"
            difficulty_display = (
                difficulty_value
                if difficulty_value is not None and detail.adversary_level
                else "—"
            )
            adversary_level_block = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            detail.adversary_name,
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_GREY_900,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            f"Nivel {level_display} · Dificultad {difficulty_display}",
                            size=14,
                            color=ft.Colors.BLUE_GREY_900,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    spacing=6,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                bgcolor=ft.Colors.BLUE_GREY_50,
                border_radius=8,
                alignment=ft.Alignment.CENTER,
            )

        setup_section = _dark_section(
            ft.Column(
                [
                    ft.Text(
                        f"Incursión {detail.index} · {detail.period_label}",
                        size=12,
                        color=ft.Colors.BLUE_GREY_200,
                    ),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(
                                        f"{detail.spirit_1_name} ({detail.board_1_name})",
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.WHITE,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Text(
                                        f"{detail.spirit_2_name} ({detail.board_2_name})",
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.WHITE,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                ],
                                spacing=4,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Text(
                        detail.layout_name,
                        size=14,
                        color=ft.Colors.BLUE_GREY_100,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    layout_preview(detail),
                    ft.Divider(color=ft.Colors.BLUE_GREY_700),
                    adversary_level_block,
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        finalize_readonly = view_model.session_state == SESSION_STATE_FINALIZED
        result_value = view_model.finalize_form.result
        is_win = result_value == "win"
        is_loss = result_value == "loss"
        formula, score_preview = view_model.score_preview()
        preview_score_text = (
            f"Puntuación: {score_preview}"
            if score_preview is not None
            else "Puntuación: —"
        )

        confirm_row = ft.Row(
            spacing=8,
            visible=(
                view_model.show_finalize_confirm
                and view_model.session_state != SESSION_STATE_FINALIZED
            ),
            controls=[
                ft.Button(
                    "Confirmar",
                    icon=ft.Icons.CHECK,
                    on_click=lambda _: view_model.finalize_incursion(service),
                    bgcolor=ft.Colors.GREEN_600,
                    color=ft.Colors.WHITE,
                ),
                ft.OutlinedButton(
                    "Cancelar",
                    icon=ft.Icons.CLOSE,
                    on_click=lambda _: view_model.toggle_finalize_confirm(False),
                ),
            ],
        )

        finalize_button = None
        if view_model.session_state != SESSION_STATE_FINALIZED:
            finalize_button = ft.OutlinedButton(
                "Finalizar incursión",
                icon=ft.Icons.FLAG,
                on_click=lambda _: view_model.toggle_finalize_confirm(True),
                disabled=False,
                style=ft.ButtonStyle(
                    color=ft.Colors.BLUE_GREY_800,
                    overlay_color=ft.Colors.BLUE_GREY_50,
                    padding=ft.Padding.symmetric(vertical=10, horizontal=14),
                    shape=ft.RoundedRectangleBorder(radius=12),
                ),
            )

        lower_block_max_width = min(560.0, max(340.0, float(page.width or 900) - 64.0))
        result_panel_width = lower_block_max_width
        sessions_table_width = max(300.0, result_panel_width - 24.0)

        grid_gap = 12
        grid_vertical_spacing = 10
        use_single_column_grid = result_panel_width < 520.0
        single_column_width = max(220.0, result_panel_width - 24.0)
        grid_column_width = max(150.0, (result_panel_width - 24.0 - grid_gap) / 2.0)

        def _result_dropdown(field_width: float) -> ft.Dropdown:
            return ft.Dropdown(
                label="Resultado",
                options=[
                    ft.dropdown.Option("win", "Victoria"),
                    ft.dropdown.Option("loss", "Derrota"),
                ],
                value=result_value,
                width=field_width,
                disabled=finalize_readonly,
                on_select=lambda event: view_model.update_finalize_field(
                    "result", event.control.value
                ),
            )

        def _dahan_alive_field(field_width: float) -> ft.TextField:
            return ft.TextField(
                label="Dahan vivos",
                value=view_model.finalize_form.dahan_alive,
                keyboard_type=ft.KeyboardType.NUMBER,
                width=field_width,
                disabled=finalize_readonly,
                on_change=lambda event: view_model.update_finalize_field(
                    "dahan_alive", event.control.value
                ),
            )

        def _blight_field(field_width: float) -> ft.TextField:
            return ft.TextField(
                label="Plaga en la isla",
                value=view_model.finalize_form.blight_on_island,
                keyboard_type=ft.KeyboardType.NUMBER,
                width=field_width,
                disabled=finalize_readonly,
                on_change=lambda event: view_model.update_finalize_field(
                    "blight_on_island", event.control.value
                ),
            )

        def _cards_field(field_width: float) -> ft.Control:
            if is_win:
                return ft.TextField(
                    label="Cartas en el mazo",
                    value=view_model.finalize_form.invader_cards_remaining,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    width=field_width,
                    disabled=finalize_readonly,
                    on_change=lambda event: view_model.update_finalize_field(
                        "invader_cards_remaining", event.control.value
                    ),
                )
            if is_loss:
                return ft.TextField(
                    label="Cartas fuera del mazo",
                    value=view_model.finalize_form.invader_cards_out_of_deck,
                    keyboard_type=ft.KeyboardType.NUMBER,
                    width=field_width,
                    disabled=finalize_readonly,
                    on_change=lambda event: view_model.update_finalize_field(
                        "invader_cards_out_of_deck", event.control.value
                    ),
                )
            return ft.Container(width=field_width)

        if use_single_column_grid:
            stacked_controls: list[ft.Control] = [
                _result_dropdown(single_column_width),
                _dahan_alive_field(single_column_width),
                _blight_field(single_column_width),
            ]
            if is_win or is_loss:
                stacked_controls.append(_cards_field(single_column_width))
            result_fields_grid: ft.Control = ft.Column(
                stacked_controls,
                spacing=grid_vertical_spacing,
            )
        else:
            left_column = ft.Container(
                width=grid_column_width,
                content=ft.Column(
                    [
                        _result_dropdown(grid_column_width),
                        _blight_field(grid_column_width),
                    ],
                    spacing=grid_vertical_spacing,
                ),
            )
            right_column = ft.Container(
                width=grid_column_width,
                content=ft.Column(
                    [
                        _dahan_alive_field(grid_column_width),
                        _cards_field(grid_column_width),
                    ],
                    spacing=grid_vertical_spacing,
                ),
            )
            result_fields_grid = ft.Row(
                [left_column, right_column],
                spacing=grid_gap,
                alignment=ft.MainAxisAlignment.START,
            )

        result_panel = ft.Container(
            width=result_panel_width,
            padding=12,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            content=ft.Column(
                [
                    ft.Text(
                        "Resultado",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_GREY_800,
                    ),
                    (
                        ft.Text(
                            (
                                f"Resultado final: {get_result_label(detail.result)} · "
                                f"Puntuación {detail.score}"
                            ),
                            size=12,
                            color=ft.Colors.BLUE_GREY_600,
                        )
                        if view_model.session_state == SESSION_STATE_FINALIZED
                        else ft.Container(height=0)
                    ),
                    result_fields_grid,
                    ft.Container(
                        padding=ft.Padding.only(top=8),
                        content=ft.Column(
                            [
                                ft.Text(
                                    f"Fórmula: {formula}",
                                    size=12,
                                    color=ft.Colors.BLUE_GREY_500,
                                ),
                                ft.Text(
                                    (
                                        f"Puntuación: {detail.score}"
                                        if finalize_readonly
                                        else preview_score_text
                                    ),
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.BLUE_GREY_700,
                                ),
                            ],
                            spacing=2,
                        ),
                    ),
                    confirm_row,
                ],
                spacing=10,
            ),
        )

        total_seconds_value = compute_total_seconds(
            view_model.sessions,
            view_model.timer_now or datetime.now(timezone.utc),
        )
        time_color = (
            ft.Colors.BLUE_600
            if view_model.open_session
            else ft.Colors.BLUE_GREY_900
        )
        time_text = ft.Text(
            f"⏱ {_format_total_time(total_seconds_value)}",
            size=28,
            weight=ft.FontWeight.BOLD,
            color=time_color,
            text_align=ft.TextAlign.CENTER,
        )

        primary_icon = "▶" if not view_model.open_session else "⏹"
        primary_label = (
            "Iniciar sesión" if not view_model.open_session else "Finalizar sesión"
        )
        primary_button = None
        if view_model.session_state != SESSION_STATE_FINALIZED:
            primary_button = ft.FilledButton(
                content=ft.Row(
                    [
                        ft.Text(primary_icon, size=18),
                        ft.Text(primary_label, size=15, weight=ft.FontWeight.BOLD),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
                height=52,
                width=320,
                on_click=lambda _: view_model.handle_session_action(service),
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.BLUE_700,
                    color=ft.Colors.WHITE,
                    padding=ft.Padding.symmetric(vertical=12, horizontal=18),
                    shape=ft.RoundedRectangleBorder(radius=14),
                ),
            )

        session_rows: list[ft.DataRow] = []
        if not view_model.sessions:
            sessions_detail: ft.Control = ft.Container(
                content=ft.Text(
                    "No hay sesiones registradas.",
                    size=12,
                    color=ft.Colors.BLUE_GREY_400,
                ),
                padding=ft.Padding.only(top=6),
                width=sessions_table_width,
            )
        else:
            for session in sorted(
                view_model.sessions,
                key=lambda s: s.ended_at or s.started_at or datetime.min,
                reverse=True,
            ):
                started_at = session.started_at
                ended_at = session.ended_at
                duration_minutes = (
                    int((ended_at - started_at).total_seconds() // 60)
                    if started_at and ended_at
                    else 0
                )
                start_date, start_time = _split_date_time(started_at)
                _, end_time = _split_date_time(ended_at)
                session_rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(
                                ft.Row(
                                    [
                                        ft.Icon(
                                            ft.Icons.CALENDAR_TODAY,
                                            size=14,
                                            color=ft.Colors.BLUE_GREY_500,
                                        ),
                                        ft.Text(
                                            start_date,
                                            size=12,
                                            color=ft.Colors.BLUE_GREY_800,
                                        ),
                                    ],
                                    spacing=4,
                                )
                            ),
                            ft.DataCell(
                                ft.Row(
                                    [
                                        ft.Icon(
                                            ft.Icons.ACCESS_TIME,
                                            size=14,
                                            color=ft.Colors.BLUE_GREY_500,
                                        ),
                                        ft.Text(
                                            f"{start_time}–{end_time or 'ahora'}",
                                            size=12,
                                            color=ft.Colors.BLUE_GREY_800,
                                        ),
                                    ],
                                    spacing=4,
                                )
                            ),
                            ft.DataCell(
                                ft.Row(
                                    [
                                        ft.Icon(
                                            ft.Icons.HOURGLASS_BOTTOM,
                                            size=14,
                                            color=ft.Colors.BLUE_GREY_500,
                                        ),
                                        ft.Text(
                                            (
                                                "—"
                                                if not ended_at
                                                else f"{duration_minutes}"
                                            ),
                                            size=12,
                                            weight=ft.FontWeight.W_600,
                                            color=ft.Colors.BLUE_GREY_900,
                                        ),
                                    ],
                                    spacing=4,
                                )
                            ),
                        ]
                    )
                )
            sessions_detail = ft.Container(
                content=ft.DataTable(
                    columns=[
                        ft.DataColumn(label=ft.Text("Fecha")),
                        ft.DataColumn(label=ft.Text("Horario")),
                        ft.DataColumn(label=ft.Text("Duración")),
                    ],
                    rows=session_rows,
                    column_spacing=18,
                    heading_row_height=0,
                    data_row_max_height=32,
                    data_row_min_height=28,
                    divider_thickness=0,
                ),
                padding=ft.Padding.only(top=6),
                width=sessions_table_width,
            )

        sessions_panel = ft.Container(
            width=result_panel_width,
            padding=12,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            content=ft.Column(
                [
                    ft.Text(
                        "Sesiones",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_GREY_800,
                    ),
                    sessions_detail,
                ],
                spacing=8,
            ),
        )

        bottom_section = ft.Container(
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            content=ft.Container(
                width=lower_block_max_width,
                content=ft.Column(
                    [
                        ft.Container(
                            content=time_text,
                            width=lower_block_max_width,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Container(
                            content=ft.Column(
                                [control for control in [primary_button, finalize_button] if control],
                                spacing=10,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            width=lower_block_max_width,
                            alignment=ft.Alignment.CENTER,
                        ),
                        result_panel,
                        sessions_panel,
                    ],
                    spacing=14,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
        )

        content = ft.Container(
            content=ft.Column(
                [
                    setup_section,
                    bottom_section,
                ],
                spacing=16,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=16,
            expand=True,
        )

    return ft.Column(
        [
            ft.AppBar(title=ft.Text("Incursión"), center_title=True),
            content,
        ],
        expand=True,
        spacing=0,
    )
