from __future__ import annotations

from datetime import datetime, timezone
import flet as ft

from app.services.firestore_service import FirestoreService
from app.services.score_service import calculate_score
from app.screens.data_lookup import (
    get_adversary_difficulty,
    get_adversary_levels,
    get_adversary_name,
    get_board_name,
    get_layout_name,
    get_spirit_name,
)
from app.utils.datetime_format import format_datetime_local
from app.utils.logger import get_logger

logger = get_logger(__name__)

SESSION_STATE_NOT_STARTED = "NOT_STARTED"
SESSION_STATE_ACTIVE = "ACTIVE"
SESSION_STATE_IDLE = "IDLE"
SESSION_STATE_FINALIZED = "FINALIZED"


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
    setup_section = ft.Container(
        padding=16,
        border_radius=16,
        border=ft.border.all(1, ft.Colors.GREY_300),
        bgcolor=ft.Colors.WHITE,
    )
    sessions_section = ft.Container(
        padding=16,
        border_radius=16,
        border=ft.border.all(1, ft.Colors.GREY_300),
        bgcolor=ft.Colors.WHITE,
    )
    result_section = ft.Container(
        padding=16,
        border_radius=16,
        border=ft.border.all(1, ft.Colors.GREY_300),
        bgcolor=ft.Colors.WHITE,
    )

    def total_minutes(sessions: list[dict]) -> int:
        logger.debug("Calculating total minutes sessions_count=%s", len(sessions))
        total_seconds = 0
        now = datetime.now(timezone.utc)
        for session in sessions:
            started = session.get("started_at")
            ended = session.get("ended_at") or now
            if started is None:
                continue
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            if ended.tzinfo is None:
                ended = ended.replace(tzinfo=timezone.utc)
            total_seconds += max(0, int((ended - started).total_seconds()))
        return int(total_seconds // 60)

    def show_message(text: str) -> None:
        logger.info("User message shown: %s", text)
        page.snack_bar = ft.SnackBar(ft.Text(text))
        page.snack_bar.open = True
        page.update()

    def close_dialog(dialog: ft.AlertDialog) -> None:
        logger.debug("Closing dialog title=%s", dialog.title)
        dialog.open = False
        page.update()

    def build_formula_text(result: str) -> str:
        if result == "win":
            return (
                "5 × dificultad + 10 + 2 × cartas restantes + "
                "jugadores × dahan vivos − jugadores × plaga"
            )
        return (
            "2 × dificultad + 1 × cartas fuera del mazo + "
            "jugadores × dahan vivos − jugadores × plaga"
        )

    def parse_int(value: str | None) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def open_sessions_detail_dialog(sessions: list[dict]) -> None:
        logger.info("Opening sessions detail dialog incursion_id=%s", incursion_id)
        items: list[ft.Control] = []
        if not sessions:
            items.append(ft.Text("No hay sesiones registradas."))
        else:
            for session in sessions:
                items.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.TIMER),
                        title=ft.Text(
                            f"{format_datetime_local(session.get('started_at'))} → "
                            f"{format_datetime_local(session.get('ended_at'))}"
                        ),
                    )
                )
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Sesiones"),
            content=ft.Column(items, tight=True, scroll=ft.ScrollMode.AUTO),
            actions=[ft.TextButton("Cerrar", on_click=lambda _: close_dialog(dialog))],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def open_score_detail_dialog(incursion: dict) -> None:
        logger.info("Opening score detail dialog incursion_id=%s", incursion_id)
        result_value = incursion.get("result")
        result_label = "Victoria" if result_value == "win" else "Derrota"
        difficulty_value = int(incursion.get("difficulty", 0) or 0)
        score_value = incursion.get("score")
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Detalle de puntuación"),
            content=ft.Column(
                [
                    ft.Text(f"Resultado: {result_label}"),
                    ft.Text(f"Dificultad: {difficulty_value}"),
                    ft.Text(f"Fórmula: {build_formula_text(result_value)}"),
                    ft.Divider(),
                    ft.Text(f"Jugadores: {incursion.get('player_count', 0)}"),
                    ft.Text(f"Dahan vivos: {incursion.get('dahan_alive', 0)}"),
                    ft.Text(f"Plaga en la isla: {incursion.get('blight_on_island', 0)}"),
                    ft.Text(
                        "Cartas invasoras restantes: "
                        f"{incursion.get('invader_cards_remaining', 0)}"
                    ),
                    ft.Text(
                        "Cartas invasoras fuera del mazo: "
                        f"{incursion.get('invader_cards_out_of_deck', 0)}"
                    ),
                    ft.Divider(),
                    ft.Text(f"Puntuación: {score_value}"),
                ],
                tight=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda _: close_dialog(dialog))],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def load_detail() -> None:
        logger.debug("Loading incursion detail")
        setup_section.content = None
        sessions_section.content = None
        result_section.content = None

        incursions = service.list_incursions(era_id, period_id)
        incursion = next(
            (item for item in incursions if item["id"] == incursion_id), None
        )
        if not incursion:
            logger.warning("Incursion not found incursion_id=%s", incursion_id)
            setup_section.content = ft.Text("Incursión no encontrada.")
            page.update()
            return
        period = next(
            (item for item in service.list_periods(era_id) if item["id"] == period_id),
            None,
        )
        period_adversaries_assigned = bool(
            period and period.get("adversaries_assigned_at")
        )
        logger.debug(
            "Period adversaries assigned=%s period_id=%s",
            period_adversaries_assigned,
            period_id,
        )

        sessions = service.list_sessions(era_id, period_id, incursion_id)
        has_open_session = any(session.get("ended_at") is None for session in sessions)
        has_started = bool(incursion.get("started_at"))
        is_finalized = bool(incursion.get("ended_at"))

        def resolve_state() -> str:
            if is_finalized:
                return SESSION_STATE_FINALIZED
            if not has_started:
                return SESSION_STATE_NOT_STARTED
            if has_open_session:
                return SESSION_STATE_ACTIVE
            return SESSION_STATE_IDLE

        state = resolve_state()
        logger.debug("Incursion status=%s", state)
        adversary_id = incursion.get("adversary_id")
        adversary_name = get_adversary_name(adversary_id)
        period_label = (
            f"Periodo {period.get('index', '—')}" if period else "Periodo —"
        )

        layout_name = get_layout_name(incursion.get("board_layout"))
        layout_chip = ft.Container(
            content=ft.Text(layout_name, size=16, weight=ft.FontWeight.BOLD),
            bgcolor=ft.Colors.BLUE_GREY_50,
            padding=ft.padding.symmetric(horizontal=14, vertical=8),
            border_radius=12,
        )

        difficulty_text = ft.Text("Dificultad: —", size=14, weight=ft.FontWeight.BOLD)
        adversary_level_control: ft.Dropdown | None = None

        def update_difficulty(event: ft.ControlEvent | None = None) -> None:
            if adversary_level_control is None:
                return
            difficulty_value = get_adversary_difficulty(
                adversary_id, adversary_level_control.value
            )
            difficulty_text.value = (
                f"Dificultad: {difficulty_value}"
                if difficulty_value is not None
                else "Dificultad: —"
            )
            page.update()

        if state == SESSION_STATE_NOT_STARTED:
            levels = get_adversary_levels(adversary_id)
            level_options = [
                ft.dropdown.Option(level.level, level.level) for level in levels
            ]
            adversary_level_control = ft.Dropdown(
                label="Nivel del adversario",
                options=level_options,
                disabled=not bool(level_options),
            )
            adversary_level_control.on_change = update_difficulty
            update_difficulty()

        setup_controls: list[ft.Control] = [
            ft.Text("Preparación", weight=ft.FontWeight.BOLD, size=16),
            ft.Text(
                f"Incursión {incursion.get('index', 0)} · {period_label}",
                size=12,
                color=ft.Colors.BLUE_GREY_400,
            ),
            ft.Text("Espíritus", size=12, color=ft.Colors.BLUE_GREY_400),
            ft.Column(
                [
                    ft.Text(
                        f"{get_spirit_name(incursion.get('spirit_1_id'))} "
                        f"({get_board_name(incursion.get('board_1'))})",
                        weight=ft.FontWeight.BOLD,
                        size=16,
                    ),
                    ft.Text(
                        f"{get_spirit_name(incursion.get('spirit_2_id'))} "
                        f"({get_board_name(incursion.get('board_2'))})",
                        weight=ft.FontWeight.BOLD,
                        size=16,
                    ),
                ],
                spacing=2,
            ),
            ft.Text("Distribución", size=12, color=ft.Colors.BLUE_GREY_400),
            ft.Container(
                content=layout_chip,
                alignment=ft.alignment.center,
            ),
            ft.Text("Adversario", size=12, color=ft.Colors.BLUE_GREY_400),
            ft.Text(adversary_name, weight=ft.FontWeight.BOLD),
        ]

        if state == SESSION_STATE_NOT_STARTED:
            setup_controls.extend(
                [
                    adversary_level_control,
                    difficulty_text,
                ]
            )
        else:
            setup_controls.extend(
                [
                    ft.Text(
                        f"Nivel: {incursion.get('adversary_level', '—')}",
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        f"Dificultad: {incursion.get('difficulty', '—')}",
                        weight=ft.FontWeight.BOLD,
                    ),
                ]
            )

        setup_section.content = ft.Column(setup_controls, spacing=8)

        def handle_fab_click(event: ft.ControlEvent) -> None:
            logger.info(
                "FAB clicked incursion_id=%s state=%s",
                incursion_id,
                state,
            )
            if state == SESSION_STATE_NOT_STARTED:
                if not period_adversaries_assigned:
                    show_message("Debes asignar adversarios del periodo.")
                    return
                if not adversary_id:
                    show_message("Debes asignar un adversario.")
                    return
                if adversary_level_control is None:
                    show_message("Debes seleccionar un nivel válido.")
                    return
                difficulty_value = get_adversary_difficulty(
                    adversary_id, adversary_level_control.value
                )
                if not adversary_level_control.value or difficulty_value is None:
                    show_message("Debes seleccionar un nivel válido.")
                    return
                try:
                    service.start_incursion(
                        era_id,
                        period_id,
                        incursion_id,
                        adversary_level_control.value,
                        difficulty_value,
                    )
                except ValueError as exc:
                    logger.error("Failed to start incursion error=%s", exc, exc_info=True)
                    show_message(str(exc))
                    return
            elif state == SESSION_STATE_ACTIVE:
                service.pause_incursion(era_id, period_id, incursion_id)
            elif state == SESSION_STATE_IDLE:
                try:
                    service.resume_incursion(era_id, period_id, incursion_id)
                except ValueError as exc:
                    logger.error("Failed to resume incursion error=%s", exc, exc_info=True)
                    show_message(str(exc))
                    return
            load_detail()
            page.update()

        if state == SESSION_STATE_FINALIZED:
            page.floating_action_button = None
        else:
            fab_icon = (
                ft.Icons.STOP
                if state == SESSION_STATE_ACTIVE
                else ft.Icons.PLAY_ARROW
            )
            fab_tooltip = (
                "Cerrar sesión" if state == SESSION_STATE_ACTIVE else "Iniciar sesión"
            )
            page.floating_action_button = ft.FloatingActionButton(
                icon=fab_icon,
                tooltip=fab_tooltip,
                on_click=handle_fab_click,
            )

        total_time = total_minutes(sessions)
        sessions_section.visible = state != SESSION_STATE_FINALIZED
        if sessions_section.visible:
            sessions_list = ft.ListView(spacing=6, expand=False)
            if not sessions:
                sessions_list.controls.append(ft.Text("No hay sesiones registradas."))
            else:
                for session in sessions:
                    sessions_list.controls.append(
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.TIMER),
                            title=ft.Text(
                                f"{format_datetime_local(session.get('started_at'))} → "
                                f"{format_datetime_local(session.get('ended_at'))}"
                            ),
                        )
                    )
            sessions_section.content = ft.Column(
                [
                    ft.Text("Sesiones", weight=ft.FontWeight.BOLD, size=16),
                    sessions_list,
                    ft.Text(f"Tiempo total: {total_time} min"),
                ],
                spacing=8,
            )

        def open_finalize_dialog(event: ft.ControlEvent) -> None:
            if state == SESSION_STATE_FINALIZED:
                show_message("La incursión ya está finalizada.")
                return
            if has_open_session:
                service.pause_incursion(era_id, period_id, incursion_id)
            difficulty_value = int(incursion.get("difficulty", 0) or 0)
            fields = {
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
            preview_difficulty = ft.Text(
                f"Dificultad: {difficulty_value}", weight=ft.FontWeight.BOLD
            )
            preview_formula = ft.Text("Fórmula: —")
            preview_score = ft.Text("Puntuación calculada: —", weight=ft.FontWeight.BOLD)

            def update_preview(event: ft.ControlEvent | None = None) -> None:
                result_value = fields["result"].value
                remaining_visible = result_value == "win"
                out_visible = result_value == "loss"
                fields["invader_cards_remaining"].visible = remaining_visible
                fields["invader_cards_out_of_deck"].visible = out_visible
                preview_formula.value = (
                    f"Fórmula: {build_formula_text(result_value)}"
                    if result_value
                    else "Fórmula: —"
                )
                player_count = parse_int(fields["player_count"].value)
                dahan_alive = parse_int(fields["dahan_alive"].value)
                blight_on_island = parse_int(fields["blight_on_island"].value)
                invader_remaining = parse_int(fields["invader_cards_remaining"].value)
                invader_out = parse_int(fields["invader_cards_out_of_deck"].value)
                if (
                    result_value
                    and player_count is not None
                    and dahan_alive is not None
                    and blight_on_island is not None
                    and (not remaining_visible or invader_remaining is not None)
                    and (not out_visible or invader_out is not None)
                ):
                    score_value = calculate_score(
                        difficulty=difficulty_value,
                        result=result_value,
                        invader_cards_remaining=invader_remaining or 0,
                        invader_cards_out_of_deck=invader_out or 0,
                        player_count=player_count,
                        dahan_alive=dahan_alive,
                        blight_on_island=blight_on_island,
                    )
                    preview_score.value = f"Puntuación calculada: {score_value}"
                else:
                    preview_score.value = "Puntuación calculada: —"
                page.update()

            for field in fields.values():
                field.on_change = update_preview
            update_preview()

            def handle_cancel_click(event: ft.ControlEvent) -> None:
                logger.info("Finalize dialog cancelled incursion_id=%s", incursion_id)
                close_dialog(dialog)

            def handle_save_click(event: ft.ControlEvent) -> None:
                result_value = fields["result"].value
                if not result_value:
                    show_message("Debes indicar el resultado.")
                    return
                player_count = parse_int(fields["player_count"].value)
                dahan_alive = parse_int(fields["dahan_alive"].value)
                blight_on_island = parse_int(fields["blight_on_island"].value)
                invader_remaining = parse_int(fields["invader_cards_remaining"].value)
                invader_out = parse_int(fields["invader_cards_out_of_deck"].value)
                if player_count is None or dahan_alive is None or blight_on_island is None:
                    show_message("Revisa los valores numéricos.")
                    return
                if result_value == "win" and invader_remaining is None:
                    show_message("Indica las cartas invasoras restantes.")
                    return
                if result_value == "loss" and invader_out is None:
                    show_message("Indica las cartas invasoras fuera del mazo.")
                    return
                try:
                    service.finalize_incursion(
                        era_id=era_id,
                        period_id=period_id,
                        incursion_id=incursion_id,
                        result=result_value,
                        player_count=player_count,
                        invader_cards_remaining=invader_remaining or 0,
                        invader_cards_out_of_deck=invader_out or 0,
                        dahan_alive=dahan_alive,
                        blight_on_island=blight_on_island,
                    )
                except ValueError:
                    logger.error(
                        "Finalize incursion failed due to numeric validation incursion_id=%s",
                        incursion_id,
                        exc_info=True,
                    )
                    show_message("Revisa los valores numéricos.")
                    return
                dialog.open = False
                load_detail()
                page.update()
                logger.info("Incursion finalized incursion_id=%s", incursion_id)

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Finalizar incursión"),
                content=ft.Column(
                    [
                        fields["result"],
                        fields["player_count"],
                        fields["dahan_alive"],
                        fields["blight_on_island"],
                        fields["invader_cards_remaining"],
                        fields["invader_cards_out_of_deck"],
                        ft.Divider(),
                        preview_difficulty,
                        preview_formula,
                        preview_score,
                    ],
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=handle_cancel_click),
                    ft.ElevatedButton("Guardar y finalizar", on_click=handle_save_click),
                ],
            )
            page.dialog = dialog
            dialog.open = True
            page.update()
            logger.debug("Finalize dialog opened incursion_id=%s", incursion_id)

        if state == SESSION_STATE_FINALIZED:
            result_value = incursion.get("result")
            result_label = "Victoria" if result_value == "win" else "Derrota"
            score_value = incursion.get("score", "—")
            summary_cards = ft.Row(
                [
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.TIMER),
                                    ft.Column(
                                        [
                                            ft.Text("Tiempo total"),
                                            ft.Text(f"{total_time} min", weight=ft.FontWeight.BOLD),
                                        ],
                                        spacing=2,
                                    ),
                                ],
                                spacing=12,
                            ),
                            padding=12,
                        ),
                        on_click=lambda _: open_sessions_detail_dialog(sessions),
                    ),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.STAR),
                                    ft.Column(
                                        [
                                            ft.Text("Puntuación"),
                                            ft.Text(
                                                str(score_value),
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                        ],
                                        spacing=2,
                                    ),
                                ],
                                spacing=12,
                            ),
                            padding=12,
                        ),
                        on_click=lambda _: open_score_detail_dialog(incursion),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                wrap=True,
            )
            result_section.content = ft.Column(
                [
                    ft.Text("Resumen", weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(f"Resultado: {result_label}"),
                    summary_cards,
                ],
                spacing=12,
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
                    ft.Text(
                        "Completa los datos para cerrar la incursión.",
                        size=12,
                        color=ft.Colors.BLUE_GREY_400,
                    ),
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
