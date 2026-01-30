from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import flet as ft

from app.screens.incursion_detail.incursion_detail_model import (
    SESSION_STATE_FINALIZED,
    compute_total_seconds,
    get_result_label,
)
from app.screens.incursion_detail.incursion_detail_viewmodel import (
    IncursionDetailViewModel,
)
from app.services.service_registry import get_firestore_service
from app.utils.debug_hud import debug_hud
from app.utils.datetime_format import format_datetime_local
from app.utils.logger import get_logger

logger = get_logger(__name__)


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
        border=ft.border.all(1, ft.Colors.GREY_300),
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
                    ft.Text(f"Jugadores: {detail.player_count}"),
                    ft.Text(f"Dahan vivos: {detail.dahan_alive}"),
                    ft.Text(f"Plaga en la isla: {detail.blight_on_island}"),
                    ft.Text(
                        f"Cartas restantes: {detail.invader_cards_remaining}"
                    ),
                    ft.Text(
                        f"Cartas fuera del mazo: {detail.invader_cards_out_of_deck}"
                    ),
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
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
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
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
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
                    ft.Container(
                        height=140,
                        width=240,
                        bgcolor=ft.Colors.BLUE_GREY_700,
                        border_radius=12,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Text(
                            "Imagen de layout",
                            color=ft.Colors.BLUE_GREY_100,
                            size=12,
                        ),
                    ),
                    ft.Divider(color=ft.Colors.BLUE_GREY_700),
                    adversary_level_block,
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

        finalize_readonly = view_model.session_state == SESSION_STATE_FINALIZED
        result_value = view_model.finalize_form.result
        formula, score_preview = view_model.score_preview()
        preview_score_text = (
            f"Puntuación: {score_preview}"
            if score_preview is not None
            else "Puntuación: —"
        )

        confirm_row = ft.Row(
            spacing=8,
            visible=view_model.show_finalize_confirm,
            controls=[
                ft.ElevatedButton(
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
                    padding=ft.padding.symmetric(vertical=10, horizontal=14),
                    shape=ft.RoundedRectangleBorder(radius=12),
                ),
            )

        invader_remaining_visible = (result_value == "win") or not finalize_readonly
        invader_out_visible = (result_value == "loss") or not finalize_readonly

        finalize_panel = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "Finalizar incursión",
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_GREY_800,
                        ),
                        ft.Row(
                            [
                                ft.Dropdown(
                                    label="Resultado",
                                    options=[
                                        ft.dropdown.Option("win", "Victoria"),
                                        ft.dropdown.Option("loss", "Derrota"),
                                    ],
                                    value=result_value,
                                    disabled=finalize_readonly,
                                    on_select=lambda event: view_model.update_finalize_field(
                                        "result", event.control.value
                                    ),
                                ),
                                ft.TextField(
                                    label="Jugadores",
                                    value=view_model.finalize_form.player_count,
                                    keyboard_type=ft.KeyboardType.NUMBER,
                                    disabled=finalize_readonly,
                                    on_change=lambda event: view_model.update_finalize_field(
                                        "player_count", event.control.value
                                    ),
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Row(
                            [
                                ft.TextField(
                                    label="Dahan vivos",
                                    value=view_model.finalize_form.dahan_alive,
                                    keyboard_type=ft.KeyboardType.NUMBER,
                                    disabled=finalize_readonly,
                                    on_change=lambda event: view_model.update_finalize_field(
                                        "dahan_alive", event.control.value
                                    ),
                                ),
                                ft.TextField(
                                    label="Plaga en la isla",
                                    value=view_model.finalize_form.blight_on_island,
                                    keyboard_type=ft.KeyboardType.NUMBER,
                                    disabled=finalize_readonly,
                                    on_change=lambda event: view_model.update_finalize_field(
                                        "blight_on_island", event.control.value
                                    ),
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Row(
                            [
                                ft.TextField(
                                    label="Cartas invasoras restantes",
                                    value=view_model.finalize_form.invader_cards_remaining,
                                    keyboard_type=ft.KeyboardType.NUMBER,
                                    disabled=finalize_readonly,
                                    visible=invader_remaining_visible,
                                    on_change=lambda event: view_model.update_finalize_field(
                                        "invader_cards_remaining", event.control.value
                                    ),
                                ),
                                ft.TextField(
                                    label="Cartas invasoras fuera del mazo",
                                    value=view_model.finalize_form.invader_cards_out_of_deck,
                                    keyboard_type=ft.KeyboardType.NUMBER,
                                    disabled=finalize_readonly,
                                    visible=invader_out_visible,
                                    on_change=lambda event: view_model.update_finalize_field(
                                        "invader_cards_out_of_deck", event.control.value
                                    ),
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Column(
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
                        confirm_row,
                    ],
                    spacing=10,
                ),
                padding=12,
            ),
            elevation=2,
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
            on_click=(
                lambda _: view_model.handle_session_action(service)
                if view_model.session_state != SESSION_STATE_FINALIZED
                else None
            ),
            disabled=view_model.session_state == SESSION_STATE_FINALIZED,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
                padding=ft.padding.symmetric(vertical=12, horizontal=18),
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
                padding=ft.padding.only(top=6),
                width=420,
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
                padding=ft.padding.only(top=6),
                width=300,
            )

        result_summary = None
        if view_model.session_state == SESSION_STATE_FINALIZED:
            result_label = get_result_label(detail.result)
            result_summary = ft.Text(
                f"Resultado final: {result_label} · Puntuación {detail.score}",
                size=12,
                color=ft.Colors.BLUE_GREY_600,
                text_align=ft.TextAlign.CENTER,
            )

        bottom_section = _light_section(
            ft.Column(
                [
                    time_text,
                    ft.Column(
                        [primary_button]
                        + ([finalize_button] if finalize_button else []),
                        spacing=10,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    result_summary if result_summary else ft.Container(),
                    finalize_panel,
                    sessions_detail,
                ],
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
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
            debug_hud(page, "Incursión"),
            content,
        ],
        expand=True,
        spacing=0,
    )
