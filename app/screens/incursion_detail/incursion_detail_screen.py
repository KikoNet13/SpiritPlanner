from __future__ import annotations

from datetime import datetime, timezone
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
    summary_tile,
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
    SESSION_STATE_FINALIZED,
    SESSION_STATE_NOT_STARTED,
    build_period_label,
    can_edit_adversary_level,
    compute_score_preview,
    get_result_label,
    get_score_formula,
    resolve_session_state,
    total_minutes,
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
    sessions_section = light_section(ft.Container())
    result_section = light_section(ft.Container())

    def load_detail() -> None:
        logger.debug("Loading incursion detail")
        sessions_section.content = None
        result_section.content = None

        incursion = get_incursion(service, era_id, period_id, incursion_id)
        if not incursion:
            logger.warning("Incursion not found incursion_id=%s", incursion_id)
            setup_section.content = ft.Text("Incursión no encontrada.")
            page.update()
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
        difficulty_text = ft.Text("Dificultad: —", size=14, color=ft.Colors.WHITE)
        difficulty_value = incursion.get("difficulty")
        can_edit_level = can_edit_adversary_level(incursion, has_sessions)
        if can_edit_level:
            levels = get_adversary_levels(incursion.get("adversary_id"))
            level_options = [
                ft.dropdown.Option(level.level, level.level) for level in levels
            ]
            adversary_level_selector = ft.Dropdown(
                label="Nivel del adversario",
                label_style=ft.TextStyle(size=14, color=ft.Colors.WHITE),
                text_style=ft.TextStyle(size=14, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.BLUE_GREY_800,
                options=level_options,
                disabled=not bool(level_options),
                width=180,
                value=incursion.get("adversary_level"),
            )

            def update_difficulty(
                event: ft.ControlEvent | None = None, persist: bool = False
            ) -> None:
                logger.debug(
                    "Updating difficulty adversary_id=%s level=%s",
                    incursion.get("adversary_id"),
                    adversary_level_selector.value if adversary_level_selector else None,
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
                page.update()

            if adversary_level_selector:
                adversary_level_selector.on_change = (
                    lambda event: update_difficulty(event, persist=True)
                )
                update_difficulty()
        else:
            difficulty_text.value = (
                f"Dificultad: {difficulty_value}"
                if difficulty_value is not None and incursion.get("adversary_level")
                else "Dificultad: —"
            )

        layout_name = get_layout_name(incursion.get("board_layout"))

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
                                ),
                                ft.Text(
                                    f"{spirit_2_name} ({board_2_name})",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE,
                                ),
                            ],
                            spacing=4,
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
                ft.Divider(color=ft.Colors.BLUE_GREY_700),
                ft.Text(
                    f"Adversario: {adversary_name}",
                    size=14,
                    color=ft.Colors.BLUE_GREY_100,
                ),
                ft.Row(
                    [
                        adversary_level_selector
                        if adversary_level_selector
                        else ft.Text(
                            f"Nivel del adversario: {incursion.get('adversary_level') or '—'}",
                            size=14,
                            color=ft.Colors.WHITE,
                        ),
                        difficulty_text,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        def handle_finalize(
            dialog: ft.AlertDialog, fields: dict[str, ft.Control]
        ) -> None:
            logger.info(
                "Finalize incursion requested incursion_id=%s result=%s",
                incursion_id,
                fields["result"].value,
            )
            if state == SESSION_STATE_FINALIZED:
                logger.warning(
                    "Finalize blocked; incursion already finalized incursion_id=%s",
                    incursion_id,
                )
                show_message(page, "La incursión ya está finalizada.")
                return
            if not fields["result"].value:
                logger.warning(
                    "Finalize blocked; missing result incursion_id=%s", incursion_id
                )
                show_message(page, "Debes indicar el resultado.")
                return
            try:
                finalize_incursion(
                    service,
                    era_id=era_id,
                    period_id=period_id,
                    incursion_id=incursion_id,
                    result=fields["result"].value,
                    player_count=int(fields["player_count"].value or 2),
                    invader_cards_remaining=int(
                        fields["invader_cards_remaining"].value or 0
                    ),
                    invader_cards_out_of_deck=int(
                        fields["invader_cards_out_of_deck"].value or 0
                    ),
                    dahan_alive=int(fields["dahan_alive"].value or 0),
                    blight_on_island=int(fields["blight_on_island"].value or 0),
                )
            except ValueError:
                logger.error(
                    "Finalize incursion failed due to numeric validation incursion_id=%s",
                    incursion_id,
                    exc_info=True,
                )
                show_message(page, "Revisa los valores numéricos.")
                return
            dialog.open = False
            load_detail()
            page.update()
            logger.info("Incursion finalized incursion_id=%s", incursion_id)

        def open_finalize_dialog(event: ft.ControlEvent) -> None:
            if state == SESSION_STATE_FINALIZED:
                logger.warning(
                    "Finalize dialog blocked; incursion finalized incursion_id=%s",
                    incursion_id,
                )
                show_message(page, "La incursión ya está finalizada.")
                return
            logger.info("Opening finalize dialog incursion_id=%s", incursion_id)
            if open_session:
                logger.info(
                    "Closing active session before finalize incursion_id=%s",
                    incursion_id,
                )
                end_session(service, era_id, period_id, incursion_id)
            difficulty_display = incursion.get("difficulty") or 0
            fields: dict[str, ft.Control] = {
                "result": ft.Dropdown(
                    label="Resultado",
                    options=[
                        ft.dropdown.Option("win", "Victoria"),
                        ft.dropdown.Option("loss", "Derrota"),
                    ],
                ),
                "player_count": ft.TextField(
                    label="Jugadores",
                    value="2",
                    keyboard_type=ft.KeyboardType.NUMBER,
                ),
                "dahan_alive": ft.TextField(
                    label="Dahan vivos",
                    keyboard_type=ft.KeyboardType.NUMBER,
                ),
                "blight_on_island": ft.TextField(
                    label="Plaga en la isla",
                    keyboard_type=ft.KeyboardType.NUMBER,
                ),
                "invader_cards_remaining": ft.TextField(
                    label="Cartas invasoras restantes",
                    keyboard_type=ft.KeyboardType.NUMBER,
                ),
                "invader_cards_out_of_deck": ft.TextField(
                    label="Cartas invasoras fuera del mazo",
                    keyboard_type=ft.KeyboardType.NUMBER,
                ),
            }

            def parse_int(field: ft.Control, default: int = 0) -> int:
                value = getattr(field, "value", None)
                try:
                    return int(value) if value not in (None, "") else default
                except ValueError:
                    return default

            formula_text = ft.Text("Fórmula: —", size=12)
            score_text = ft.Text("Puntuación: —", size=12, weight=ft.FontWeight.BOLD)
            difficulty_text_modal = ft.Text(
                f"Dificultad: {difficulty_display}", size=12
            )

            def update_score_preview(event: ft.ControlEvent | None = None) -> None:
                result_value = fields["result"].value
                player_count = parse_int(fields["player_count"], 2)
                dahan_alive = parse_int(fields["dahan_alive"])
                blight_on_island = parse_int(fields["blight_on_island"])
                invader_remaining = parse_int(fields["invader_cards_remaining"])
                invader_out = parse_int(fields["invader_cards_out_of_deck"])
                formula, score_value = compute_score_preview(
                    result_value,
                    difficulty_display,
                    player_count,
                    dahan_alive,
                    blight_on_island,
                    invader_remaining,
                    invader_out,
                )
                formula_text.value = f"Fórmula: {formula}"
                score_text.value = (
                    f"Puntuación: {score_value}" if score_value is not None else "Puntuación: —"
                )
                fields["invader_cards_remaining"].visible = result_value == "win"
                fields["invader_cards_out_of_deck"].visible = result_value == "loss"
                page.update()

            for field_key in [
                "result",
                "player_count",
                "dahan_alive",
                "blight_on_island",
                "invader_cards_remaining",
                "invader_cards_out_of_deck",
            ]:
                field = fields[field_key]
                field.on_change = update_score_preview

            update_score_preview()

            def handle_cancel_click(event: ft.ControlEvent) -> None:
                logger.info("Finalize dialog cancelled incursion_id=%s", incursion_id)
                close_dialog(page, dialog)

            def handle_save_click(event: ft.ControlEvent) -> None:
                handle_finalize(dialog, fields)

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Finalizar incursión"),
                content=ft.Column(
                    [
                        ft.Text("Resultado", weight=ft.FontWeight.BOLD),
                        fields["result"],
                        ft.Text("Datos comunes", weight=ft.FontWeight.BOLD),
                        fields["player_count"],
                        fields["dahan_alive"],
                        fields["blight_on_island"],
                        ft.Text("Datos condicionales", weight=ft.FontWeight.BOLD),
                        fields["invader_cards_remaining"],
                        fields["invader_cards_out_of_deck"],
                        ft.Divider(),
                        ft.Text("Vista previa", weight=ft.FontWeight.BOLD),
                        difficulty_text_modal,
                        formula_text,
                        score_text,
                    ],
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=handle_cancel_click),
                    ft.ElevatedButton(
                        "Guardar y finalizar",
                        on_click=handle_save_click,
                    ),
                ],
            )
            page.dialog = dialog
            dialog.open = True
            page.update()
            logger.debug("Finalize dialog opened incursion_id=%s", incursion_id)

        def handle_session_fab(event: ft.ControlEvent) -> None:
            logger.info(
                "Session FAB clicked incursion_id=%s state=%s open=%s",
                incursion_id,
                state,
                open_session,
            )
            if state == SESSION_STATE_FINALIZED:
                return
            if open_session:
                end_session(service, era_id, period_id, incursion_id)
                load_detail()
                page.update()
                return
            if state == SESSION_STATE_NOT_STARTED:
                adversary_level = (
                    adversary_level_selector.value
                    if adversary_level_selector
                    else incursion.get("adversary_level")
                )
                if not adversary_level:
                    logger.warning("Cannot start incursion; invalid adversary level")
                    show_message(page, "Debes seleccionar un nivel válido.")
                    return
                if incursion.get("difficulty") is None:
                    show_message(page, "Debes seleccionar un nivel válido.")
                    return
                try:
                    start_session(
                        service,
                        era_id,
                        period_id,
                        incursion_id,
                    )
                except ValueError as exc:
                    logger.error(
                        "Failed to start incursion error=%s", exc, exc_info=True
                    )
                    show_message(page, str(exc))
                    return
            else:
                start_session(service, era_id, period_id, incursion_id)
            load_detail()
            page.update()

        if state == SESSION_STATE_FINALIZED:
            page.floating_action_button = None
            page.bottom_appbar = None
        else:
            button_label = "Finalizar sesión" if open_session else "Iniciar sesión"
            page.floating_action_button = None
            page.bottom_appbar = ft.BottomAppBar(
                content=ft.Container(
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                button_label,
                                on_click=handle_session_fab,
                                icon=ft.Icons.TIMER,
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    padding=ft.padding.symmetric(vertical=10),
                )
            )

        def open_sessions_dialog(event: ft.ControlEvent) -> None:
            sessions_list = ft.ListView(spacing=6, expand=False)
            if not sessions:
                sessions_list.controls.append(ft.Text("No hay sesiones registradas."))
            else:
                for session in sessions:
                    sessions_list.controls.append(
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.TIMER),
                            title=ft.Text(
                                f"{format_datetime_local(session.get('started_at'))} → {format_datetime_local(session.get('ended_at'))}"
                            ),
                        )
                    )
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Detalle de sesiones"),
                content=ft.Column([sessions_list], tight=True),
                actions=[
                    ft.TextButton(
                        "Cerrar", on_click=lambda _: close_dialog(page, dialog)
                    )
                ],
            )
            page.dialog = dialog
            dialog.open = True
            page.update()

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
                        ft.Text(f"Jugadores: {incursion.get('player_count')}"),
                        ft.Text(f"Dahan vivos: {incursion.get('dahan_alive')}"),
                        ft.Text(f"Plaga en la isla: {incursion.get('blight_on_island')}"),
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

        now = datetime.now(timezone.utc)
        total_time = total_minutes(sessions, now)
        sessions_section.visible = state != SESSION_STATE_FINALIZED
        sessions_section.content = ft.Column(
            [
                ft.Text("Sesiones", weight=ft.FontWeight.BOLD, size=16),
                ft.Text(f"Duración total: {total_time} min"),
                ft.TextButton(
                    "Ver detalle de sesiones",
                    icon=ft.Icons.TIMER,
                    on_click=open_sessions_dialog,
                ),
            ],
            spacing=8,
        )

        if state == SESSION_STATE_FINALIZED:
            result_value = incursion.get("result")
            result_label = get_result_label(result_value)
            result_section.content = ft.Column(
                [
                    ft.Text("Resumen final", weight=ft.FontWeight.BOLD, size=16),
                    ft.Row(
                        [
                            summary_tile(
                                ft.Icons.TIMER,
                                f"{total_time} min",
                                open_sessions_dialog,
                            ),
                            summary_tile(
                                ft.Icons.STAR,
                                f"{incursion.get('score')}",
                                open_score_dialog,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(f"Resultado: {result_label}"),
                ],
                spacing=8,
            )
        else:
            finalize_button = ft.ElevatedButton(
                "Finalizar incursión",
                icon=ft.Icons.FLAG,
                on_click=open_finalize_dialog,
                disabled=state == SESSION_STATE_NOT_STARTED,
            )
            result_section.content = ft.Column(
                [
                    ft.Text("Resultado", weight=ft.FontWeight.BOLD, size=16),
                    ft.Text("Completa los datos para cerrar la incursión."),
                    finalize_button,
                ],
                spacing=8,
            )

        page.update()
        logger.debug("Incursion detail loaded incursion_id=%s", incursion_id)

    load_detail()

    logger.debug("Exiting incursion_detail_view incursion_id=%s", incursion_id)
    return ft.Column(
        [
            ft.AppBar(title=ft.Text("Incursión"), center_title=True),
            ft.Container(
                content=ft.Column(
                    [
                        setup_section,
                        sessions_section,
                        result_section,
                    ],
                    expand=True,
                    spacing=16,
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=16,
                expand=True,
            ),
        ],
        expand=True,
        spacing=0,
    )
