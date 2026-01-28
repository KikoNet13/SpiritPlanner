from __future__ import annotations

from datetime import datetime, timezone
import asyncio
import flet as ft

from app.screens.data_lookup import (
    get_adversary_difficulty,
    get_adversary_levels,
    get_adversary_name,
    get_board_name,
    get_layout_name,
    get_spirit_name,
)
from app.screens.incursion_detail.incursion_detail_components import (
    dark_section,
    light_section,
)
from app.screens.incursion_detail.incursion_detail_handlers import (
    close_dialog,
    finalize_incursion,
    get_incursion,
    get_period,
    list_sessions,
    end_session,
    show_message,
    start_session,
    update_adversary_level,
)
from app.screens.incursion_detail.incursion_detail_state import (
    SESSION_STATE_BETWEEN_SESSIONS,
    SESSION_STATE_FINALIZED,
    SESSION_STATE_NOT_STARTED,
    build_period_label,
    can_edit_adversary_level,
    compute_score_preview,
    get_result_label,
    get_score_formula,
    resolve_session_state,
)
from app.services.firestore_service import FirestoreService
from app.utils.datetime_format import format_datetime_local
from app.utils.logger import get_logger

logger = get_logger(__name__)


def incursion_detail_view(
    page: ft.Page,
    service: FirestoreService,
    era_id: str,
    period_id: str,
    incursion_id: str,
) -> ft.Control:
    logger.debug(
        "Entering incursion_detail_view era_id=%s period_id=%s incursion_id=%s",
        era_id,
        period_id,
        incursion_id,
    )
    setup_section = dark_section(ft.Container())
    bottom_section = light_section(ft.Container())
    timer_task = None

    def load_detail() -> None:
        logger.debug("Loading incursion detail")
        bottom_section.content = None

        incursion = get_incursion(service, era_id, period_id, incursion_id)
        if not incursion:
            logger.warning("Incursion not found incursion_id=%s", incursion_id)
            setup_section.content = ft.Text("Incursión no encontrada.")
            setup_section.update()
            bottom_section.update()
            return
        period = get_period(service, era_id, period_id)
        period_adversaries_assigned = bool(
            period and period.get("adversaries_assigned_at")
        )
        logger.debug(
            "Period adversaries assigned=%s period_id=%s",
            period_adversaries_assigned,
            period_id,
        )

        sessions = list_sessions(service, era_id, period_id, incursion_id)
        open_session = any(session.get("ended_at") is None for session in sessions)
        has_sessions = len(sessions) > 0
        logger.debug(
            "Sessions loaded count=%s open_session=%s",
            len(sessions),
            open_session,
        )

        state = resolve_session_state(incursion, has_sessions, open_session)

        spirit_1_name = get_spirit_name(incursion.get("spirit_1_id"))
        spirit_2_name = get_spirit_name(incursion.get("spirit_2_id"))
        board_1_name = get_board_name(incursion.get("board_1"))
        board_2_name = get_board_name(incursion.get("board_2"))
        adversary_name = get_adversary_name(incursion.get("adversary_id"))
        period_label = build_period_label(period)

        adversary_level_selector = None
        difficulty_text = ft.Text(
            "Dificultad: —", size=14, color=ft.Colors.BLUE_GREY_900
        )
        difficulty_value = incursion.get("difficulty")
        adversary_level_block = None
        can_edit_level = can_edit_adversary_level(incursion, has_sessions)
        if can_edit_level:
            levels = get_adversary_levels(incursion.get("adversary_id"))
            level_options = [
                ft.dropdown.Option(
                    level.level,
                    f"Nivel {level.level}",
                )
                for level in levels
            ]
            adversary_level_selector = ft.Dropdown(
                text_style=ft.TextStyle(size=14, color=ft.Colors.BLUE_GREY_900),
                bgcolor=ft.Colors.WHITE,
                options=level_options,
                disabled=not bool(level_options),
                width=220,
                value=incursion.get("adversary_level"),
            )

            def update_difficulty(
                event: ft.ControlEvent | None = None, persist: bool = False
            ) -> None:
                logger.debug(
                    "Updating difficulty adversary_id=%s level=%s",
                    incursion.get("adversary_id"),
                    (
                        adversary_level_selector.value
                        if adversary_level_selector
                        else None
                    ),
                )
                selected_level = (
                    adversary_level_selector.value if adversary_level_selector else None
                )
                computed = get_adversary_difficulty(
                    incursion.get("adversary_id"),
                    selected_level,
                )
                difficulty_text.value = (
                    f"Dificultad: {computed}"
                    if computed is not None and selected_level
                    else "Dificultad: —"
                )
                if persist:
                    try:
                        update_adversary_level(
                            service,
                            era_id=era_id,
                            period_id=period_id,
                            incursion_id=incursion_id,
                            adversary_id=incursion.get("adversary_id"),
                            adversary_level=selected_level,
                            difficulty=computed,
                        )
                        incursion["adversary_level"] = selected_level
                        incursion["difficulty"] = computed
                    except ValueError as exc:
                        logger.error(
                            "Failed to update adversary level error=%s",
                            exc,
                            exc_info=True,
                        )
                        show_message(page, str(exc))
                if adversary_level_block:
                    adversary_level_block.update()
                else:
                    difficulty_text.update()

            if adversary_level_selector:
                adversary_level_selector.on_change = lambda event: update_difficulty(
                    event, persist=True
                )
        else:
            difficulty_text.value = (
                f"Dificultad: {difficulty_value}"
                if difficulty_value is not None and incursion.get("adversary_level")
                else "Dificultad: —"
            )

        layout_name = get_layout_name(incursion.get("board_layout"))
        level_display = incursion.get("adversary_level") or "—"
        difficulty_display = (
            difficulty_value
            if difficulty_value is not None and incursion.get("adversary_level")
            else "—"
        )
        adversary_level_block = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        adversary_name,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_GREY_900,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    (
                        adversary_level_selector
                        if adversary_level_selector
                        else ft.Text(
                            f"Nivel {level_display} · Dificultad {difficulty_display}",
                            size=14,
                            color=ft.Colors.BLUE_GREY_900,
                            text_align=ft.TextAlign.CENTER,
                        )
                    ),
                    difficulty_text if adversary_level_selector else ft.Container(),
                ],
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.Colors.BLUE_GREY_50,
            border_radius=8,
            alignment=ft.Alignment.CENTER,
        )
        if adversary_level_selector:
            update_difficulty()

        setup_section.content = ft.Column(
            [
                ft.Text(
                    f"Incursión {incursion.get('index', 0)} · {period_label}",
                    size=12,
                    color=ft.Colors.BLUE_GREY_200,
                ),
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(
                                    f"{spirit_1_name} ({board_1_name})",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Text(
                                    f"{spirit_2_name} ({board_2_name})",
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
                    layout_name,
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

        # Panel inline de finalización (sin modales)
        finalize_form_fields: dict[str, ft.Control] = {}

        def parse_int(field: ft.Control, default: int = 0) -> int:
            value = getattr(field, "value", None)
            try:
                return int(value) if value not in (None, "") else default
            except ValueError:
                return default

        def parse_int_strict(field: ft.Control, default: int = 0) -> int | None:
            value = getattr(field, "value", None)
            if value in (None, ""):
                return default
            try:
                return int(value)
            except ValueError:
                return None

        def build_finalize_fields(readonly: bool) -> dict[str, ft.Control]:
            fields_local: dict[str, ft.Control] = {
                "result": ft.Dropdown(
                    label="Resultado",
                    options=[
                        ft.dropdown.Option("win", "Victoria"),
                        ft.dropdown.Option("loss", "Derrota"),
                    ],
                    value=incursion.get("result"),
                    disabled=readonly,
                ),
                "player_count": ft.TextField(
                    label="Jugadores",
                    value=str(incursion.get("player_count") or 2),
                    keyboard_type=ft.KeyboardType.NUMBER,
                    disabled=readonly,
                ),
                "dahan_alive": ft.TextField(
                    label="Dahan vivos",
                    value=str(incursion.get("dahan_alive") or ""),
                    keyboard_type=ft.KeyboardType.NUMBER,
                    disabled=readonly,
                ),
                "blight_on_island": ft.TextField(
                    label="Plaga en la isla",
                    value=str(incursion.get("blight_on_island") or ""),
                    keyboard_type=ft.KeyboardType.NUMBER,
                    disabled=readonly,
                ),
                "invader_cards_remaining": ft.TextField(
                    label="Cartas invasoras restantes",
                    value=str(incursion.get("invader_cards_remaining") or ""),
                    keyboard_type=ft.KeyboardType.NUMBER,
                    disabled=readonly,
                    visible=(incursion.get("result") or "") == "win" or not readonly,
                ),
                "invader_cards_out_of_deck": ft.TextField(
                    label="Cartas invasoras fuera del mazo",
                    value=str(incursion.get("invader_cards_out_of_deck") or ""),
                    keyboard_type=ft.KeyboardType.NUMBER,
                    disabled=readonly,
                    visible=(incursion.get("result") or "") == "loss" or not readonly,
                ),
            }
            return fields_local

        def compute_preview_and_update(
            fields_map: dict[str, ft.Control], score_label: ft.Text, formula_label: ft.Text
        ) -> None:
            result_value = fields_map["result"].value
            player_count = parse_int(fields_map["player_count"], 2)
            dahan_alive = parse_int(fields_map["dahan_alive"])
            blight_on_island = parse_int(fields_map["blight_on_island"])
            invader_remaining = parse_int(fields_map["invader_cards_remaining"])
            invader_out = parse_int(fields_map["invader_cards_out_of_deck"])
            difficulty_display = incursion.get("difficulty") or 0
            formula, score_value = compute_score_preview(
                result_value,
                difficulty_display,
                player_count,
                dahan_alive,
                blight_on_island,
                invader_remaining,
                invader_out,
            )
            formula_label.value = f"Fórmula: {formula}"
            score_label.value = (
                f"Puntuación: {score_value}" if score_value is not None else "Puntuación: —"
            )
            fields_map["invader_cards_remaining"].visible = result_value == "win"
            fields_map["invader_cards_out_of_deck"].visible = result_value == "loss"
            formula_label.update()
            score_label.update()
            fields_map["invader_cards_remaining"].update()
            fields_map["invader_cards_out_of_deck"].update()

        # Estado de confirmación inline
        confirm_row = ft.Row(spacing=8, visible=False)

        def toggle_confirm(show: bool) -> None:
            confirm_row.visible = show
            confirm_row.update()

        def handle_finalize_inline(event: ft.ControlEvent | None = None) -> None:
            if state == SESSION_STATE_FINALIZED:
                show_message(page, "La incursión ya está finalizada.")
                return
            result_value = finalize_form_fields["result"].value
            if not result_value:
                show_message(page, "Debes indicar el resultado.")
                return
            player_count = parse_int_strict(finalize_form_fields["player_count"], 2)
            invader_remaining = parse_int_strict(
                finalize_form_fields["invader_cards_remaining"], 0
            )
            invader_out = parse_int_strict(
                finalize_form_fields["invader_cards_out_of_deck"], 0
            )
            dahan_alive = parse_int_strict(finalize_form_fields["dahan_alive"], 0)
            blight_on_island = parse_int_strict(
                finalize_form_fields["blight_on_island"], 0
            )
            if None in (
                player_count,
                invader_remaining,
                invader_out,
                dahan_alive,
                blight_on_island,
            ):
                show_message(page, "Revisa los valores numéricos.")
                return
            if open_session:
                logger.info(
                    "Closing active session before finalize incursion_id=%s",
                    incursion_id,
                )
                end_session(service, era_id, period_id, incursion_id)
            try:
                finalize_incursion(
                    service,
                    era_id=era_id,
                    period_id=period_id,
                    incursion_id=incursion_id,
                    result=result_value,
                    player_count=player_count,
                    invader_cards_remaining=invader_remaining,
                    invader_cards_out_of_deck=invader_out,
                    dahan_alive=dahan_alive,
                    blight_on_island=blight_on_island,
                )
            except ValueError:
                show_message(page, "Revisa los valores numéricos.")
                return
            toggle_confirm(False)
            load_detail()
            logger.info("Incursion finalized incursion_id=%s", incursion_id)

        def handle_cancel_inline(event: ft.ControlEvent | None = None) -> None:
            toggle_confirm(False)

        # Construcción del panel inline de finalización
        finalize_readonly = state == SESSION_STATE_FINALIZED
        finalize_form_fields = build_finalize_fields(finalize_readonly)
        preview_formula = ft.Text("Fórmula: —", size=12, color=ft.Colors.BLUE_GREY_500)
        preview_score = ft.Text(
            "Puntuación: —",
            size=12,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_GREY_500,
        )

        for key in finalize_form_fields:
            field = finalize_form_fields[key]
            if hasattr(field, "on_change") and not finalize_readonly:
                field.on_change = lambda e, ff=finalize_form_fields: compute_preview_and_update(
                    ff, preview_score, preview_formula
                )

        if not finalize_readonly:
            compute_preview_and_update(finalize_form_fields, preview_score, preview_formula)
        else:
            preview_score.value = f"Puntuación: {incursion.get('score')}"
            preview_score.color = ft.Colors.BLUE_GREY_700
            preview_formula.value = "Fórmula: —"
            preview_formula.color = ft.Colors.BLUE_GREY_500

        confirm_row.controls = [
            ft.ElevatedButton(
                "Confirmar",
                icon=ft.Icons.CHECK,
                on_click=handle_finalize_inline,
                bgcolor=ft.Colors.GREEN_600,
                color=ft.Colors.WHITE,
            ),
            ft.OutlinedButton(
                "Cancelar",
                icon=ft.Icons.CLOSE,
                on_click=handle_cancel_inline,
            ),
        ]

        secondary_button = None
        if state != SESSION_STATE_FINALIZED:
            secondary_button = ft.OutlinedButton(
                "Finalizar incursión",
                icon=ft.Icons.FLAG,
                on_click=lambda _: toggle_confirm(True),
                disabled=False,
                style=ft.ButtonStyle(
                    color=ft.Colors.BLUE_GREY_800,
                    overlay_color=ft.Colors.BLUE_GREY_50,
                    padding=ft.padding.symmetric(vertical=10, horizontal=14),
                    shape=ft.RoundedRectangleBorder(radius=12),
                ),
            )

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
                                finalize_form_fields["result"],
                                finalize_form_fields["player_count"],
                            ],
                            spacing=8,
                        ),
                        ft.Row(
                            [
                                finalize_form_fields["dahan_alive"],
                                finalize_form_fields["blight_on_island"],
                            ],
                            spacing=8,
                        ),
                        ft.Row(
                            [
                                finalize_form_fields["invader_cards_remaining"],
                                finalize_form_fields["invader_cards_out_of_deck"],
                            ],
                            spacing=8,
                        ),
                        ft.Column(
                            [preview_formula, preview_score],
                            spacing=2,
                        ),
                        ft.Container(),
                        confirm_row,
                    ],
                    spacing=10,
                ),
                padding=12,
            ),
            elevation=2,
        )

        def handle_session_action(event: ft.ControlEvent) -> None:
            logger.info(
                "Session action clicked incursion_id=%s state=%s open=%s",
                incursion_id,
                state,
                open_session,
            )
            if state == SESSION_STATE_FINALIZED:
                show_message(page, "La incursión ya está finalizada.")
                return
            if open_session:
                end_session(service, era_id, period_id, incursion_id)
                load_detail()
                return
            adversary_level = (
                adversary_level_selector.value
                if adversary_level_selector
                else incursion.get("adversary_level")
            )
            if not adversary_level or incursion.get("difficulty") is None:
                logger.warning("Cannot start incursion; invalid adversary level")
                show_message(page, "Debes seleccionar un nivel válido.")
                return
            if state == SESSION_STATE_BETWEEN_SESSIONS:
                logger.debug("Resuming session incursion_id=%s", incursion_id)
            elif state != SESSION_STATE_NOT_STARTED:
                logger.debug("Starting session incursion_id=%s", incursion_id)
            try:
                start_session(
                    service,
                    era_id,
                    period_id,
                    incursion_id,
                )
            except ValueError as exc:
                logger.error("Failed to start incursion error=%s", exc, exc_info=True)
                show_message(page, str(exc))
                return
            load_detail()

        page.floating_action_button = None
        page.bottom_appbar = None

        def open_score_dialog(event: ft.ControlEvent) -> None:
            result_value = incursion.get("result")
            result_label = get_result_label(result_value)
            difficulty_value = incursion.get("difficulty") or 0
            formula = get_score_formula(result_value)
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Detalle de puntuación"),
                content=ft.Column(
                    [
                        ft.Text(f"Resultado: {result_label}"),
                        ft.Text(f"Dificultad: {difficulty_value}"),
                        ft.Text(
                            f"Jugadores: {incursion.get('player_count')}",
                        ),
                        ft.Text(
                            f"Dahan vivos: {incursion.get('dahan_alive')}",
                        ),
                        ft.Text(
                            f"Plaga en la isla: {incursion.get('blight_on_island')}"
                        ),
                        ft.Text(
                            f"Cartas restantes: {incursion.get('invader_cards_remaining')}"
                        ),
                        ft.Text(
                            f"Cartas fuera del mazo: {incursion.get('invader_cards_out_of_deck')}"
                        ),
                        ft.Text(f"Fórmula: {formula}"),
                        ft.Text(
                            f"Puntuación: {incursion.get('score')}",
                            weight=ft.FontWeight.BOLD,
                        ),
                    ],
                    tight=True,
                ),
                actions=[
                    ft.TextButton(
                        "Cerrar", on_click=lambda _: close_dialog(page, dialog)
                    )
                ],
            )
            page.dialog = dialog
            dialog.open = True
            page.update()

        # ---------- Bottom unified UI ----------
        nonlocal timer_task

        def to_utc(dt: datetime | None) -> datetime | None:
            if dt is None:
                return None
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

        def compute_total_seconds(reference: datetime | None = None) -> int:
            ref = reference or datetime.now(timezone.utc)
            total_seconds = 0
            for session in sessions:
                started_at = to_utc(session.get("started_at"))
                ended_at = to_utc(session.get("ended_at")) or ref
                if started_at and ended_at:
                    total_seconds += int((ended_at - started_at).total_seconds())
            return max(total_seconds, 0)

        def format_total_time(total_seconds: int) -> str:
            minutes, seconds = divmod(total_seconds, 60)
            return f"{minutes}:{seconds:02d}"

        def format_short_datetime(value: datetime | str | None) -> str:
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

        def session_reference_datetime(session: dict) -> datetime | None:
            return to_utc(session.get("ended_at")) or to_utc(session.get("started_at"))

        total_seconds_value = compute_total_seconds()
        time_color = ft.Colors.BLUE_600 if open_session else ft.Colors.BLUE_GREY_900
        time_text = ft.Text(
            f"⏱ {format_total_time(total_seconds_value)}",
            size=28,
            weight=ft.FontWeight.BOLD,
            color=time_color,
            text_align=ft.TextAlign.CENTER,
            data="running" if open_session else "idle",
        )

        async def tick_time() -> None:
            while time_text.data == "running":
                now_tick = datetime.now(timezone.utc)
                time_text.value = (
                    f"⏱ {format_total_time(compute_total_seconds(now_tick))}"
                )
                time_text.update()
                await asyncio.sleep(1)

        if timer_task and not timer_task.done():
            timer_task.cancel()
            timer_task = None
        if open_session and state != SESSION_STATE_FINALIZED:
            if hasattr(page, "run_task"):
                timer_task = page.run_task(tick_time)
            else:
                timer_task = asyncio.create_task(tick_time())

        primary_icon = "▶" if not open_session else "⏹"
        primary_label = "Iniciar sesión" if not open_session else "Finalizar sesión"
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
                handle_session_action if state != SESSION_STATE_FINALIZED else None
            ),
            disabled=state == SESSION_STATE_FINALIZED,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
                padding=ft.padding.symmetric(vertical=12, horizontal=18),
                shape=ft.RoundedRectangleBorder(radius=14),
            ),
        )

        secondary_button = None

        def split_date_time(dt: datetime | str | None) -> tuple[str, str]:
            display = format_short_datetime(dt)
            if "·" in display:
                date_part, time_part = [p.strip() for p in display.split("·", 1)]
            else:
                date_part, time_part = display, ""
            return date_part[:8], time_part

        session_rows: list[ft.DataRow] = []
        if not sessions:
            sessions_detail = ft.Container(
                content=ft.Text(
                    "No hay sesiones registradas.",
                    size=12,
                    color=ft.Colors.BLUE_GREY_400,
                ),
                padding=ft.padding.only(top=6),
                width=420,
            )
        else:
            sessions_sorted = sorted(
                sessions,
                key=lambda s: session_reference_datetime(s)
                or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
            )
            for session in sessions_sorted:
                started_at = to_utc(session.get("started_at"))
                ended_at = to_utc(session.get("ended_at"))
                duration_minutes = (
                    int((ended_at - started_at).total_seconds() // 60)
                    if started_at and ended_at
                    else 0
                )
                start_date, start_time = split_date_time(started_at)
                _, end_time = split_date_time(ended_at)
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

        result_value = incursion.get("result")
        result_summary = None
        if state == SESSION_STATE_FINALIZED:
            result_label = get_result_label(result_value)
            result_summary = ft.Text(
                f"Resultado final: {result_label} · Puntuación {incursion.get('score')}",
                size=12,
                color=ft.Colors.BLUE_GREY_600,
                text_align=ft.TextAlign.CENTER,
            )

        bottom_section.content = ft.Column(
            [
                time_text,
                ft.Column(
                    [primary_button] + ([secondary_button] if secondary_button else []),
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

        setup_section.update()
        bottom_section.update()
        logger.debug("Incursion detail loaded incursion_id=%s", incursion_id)

    load_detail()

    logger.debug("Exiting incursion_detail_view incursion_id=%s", incursion_id)
    main_content = ft.Container(
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
            main_content,
        ],
        expand=True,
        spacing=0,
    )
