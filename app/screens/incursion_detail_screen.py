from __future__ import annotations

from datetime import datetime, timezone
import flet as ft

from app.services.firestore_service import FirestoreService
from app.screens.data_lookup import (
    get_adversary_difficulty,
    get_adversary_levels,
    get_adversary_name,
    get_board_name,
    get_layout_name,
    get_spirit_name,
)
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
    header_container = ft.Container(
        padding=20,
        border_radius=20,
        bgcolor=ft.Colors.BLUE_GREY_900,
    )
    board_placeholder = ft.Container(
        padding=24,
        border_radius=18,
        border=ft.border.all(1, ft.Colors.BLUE_GREY_200),
        bgcolor=ft.Colors.BLUE_GREY_50,
        height=220,
    )
    data_section = ft.Container(
        padding=16,
        border_radius=16,
        border=ft.border.all(1, ft.Colors.GREY_300),
        bgcolor=ft.Colors.WHITE,
    )
    actions_section = ft.Container(
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

    def status_chip(label: str, color: str) -> ft.Container:
        logger.debug("Building status_chip label=%s color=%s", label, color)
        return ft.Container(
            content=ft.Text(label, size=12, color=ft.Colors.WHITE),
            bgcolor=color,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=12,
        )

    def format_ts(value: datetime | None) -> str:
        logger.debug("Formatting timestamp value=%s", value)
        if not value:
            return "—"
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

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

    def load_detail() -> None:
        logger.debug("Loading incursion detail")
        data_section.content = None
        actions_section.content = None
        sessions_section.content = None
        result_section.content = None

        incursions = service.list_incursions(era_id, period_id)
        incursion = next(
            (item for item in incursions if item["id"] == incursion_id), None
        )
        if not incursion:
            logger.warning("Incursion not found incursion_id=%s", incursion_id)
            data_section.content = ft.Text("Incursión no encontrada.")
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
        open_session = any(session.get("ended_at") is None for session in sessions)
        logger.debug("Sessions loaded count=%s open_session=%s", len(sessions), open_session)

        status = "No iniciado"
        status_color = ft.Colors.GREY_500
        if incursion.get("ended_at"):
            status = "Finalizado"
            status_color = ft.Colors.BLUE_600
        elif incursion.get("started_at"):
            status = "Activo"
            status_color = ft.Colors.GREEN_600
        logger.debug("Incursion status=%s", status)

        spirit_names = (
            f"{get_spirit_name(incursion.get('spirit_1_id'))} / "
            f"{get_spirit_name(incursion.get('spirit_2_id'))}"
        )
        adversary_name = get_adversary_name(incursion.get("adversary_id"))
        period_label = (
            f"Periodo {period.get('index', '—')}" if period else "Periodo —"
        )

        header_container.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(
                            spirit_names,
                            weight=ft.FontWeight.BOLD,
                            size=26,
                            color=ft.Colors.WHITE,
                        ),
                        status_chip(status, status_color),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text(
                    f"Adversario: {adversary_name}",
                    size=14,
                    color=ft.Colors.BLUE_GREY_100,
                ),
                ft.Text(
                    f"Incursión {incursion.get('index', 0)} · {period_label}",
                    size=12,
                    color=ft.Colors.BLUE_GREY_200,
                ),
                ft.Row(
                    [
                        ft.Text(
                            f"Inicio: {format_ts(incursion.get('started_at'))}",
                            size=12,
                            color=ft.Colors.BLUE_GREY_200,
                        ),
                        ft.Text(
                            f"Fin: {format_ts(incursion.get('ended_at'))}",
                            size=12,
                            color=ft.Colors.BLUE_GREY_200,
                        ),
                    ],
                    spacing=16,
                    wrap=True,
                ),
            ],
            spacing=8,
        )

        board_placeholder.content = ft.Column(
            [
                ft.Icon(
                    ft.Icons.MAP_OUTLINED,
                    size=42,
                    color=ft.Colors.BLUE_GREY_400,
                ),
                ft.Text(
                    "Composición del tablero",
                    weight=ft.FontWeight.BOLD,
                    size=16,
                ),
                ft.Text(
                    "Aquí se mostrará la imagen o layout completo de la isla.",
                    size=12,
                    color=ft.Colors.BLUE_GREY_400,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )

        data_section.content = ft.Column(
            [
                ft.Text("Datos clave", weight=ft.FontWeight.BOLD, size=16),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.GROUP),
                    title=ft.Text("Espíritus"),
                    subtitle=ft.Text(spirit_names),
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.DASHBOARD),
                    title=ft.Text("Tableros usados"),
                    subtitle=ft.Text(
                        f"{get_board_name(incursion.get('board_1'))} + "
                        f"{get_board_name(incursion.get('board_2'))}"
                    ),
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.VIEW_QUILT),
                    title=ft.Text("Distribución del mapa"),
                    subtitle=ft.Text(get_layout_name(incursion.get("board_layout"))),
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.EVENT_NOTE),
                    title=ft.Text("Periodo"),
                    subtitle=ft.Text(period_label),
                ),
            ],
            spacing=6,
        )

        if not incursion.get("started_at"):
            adversary_id = incursion.get("adversary_id")
            levels = get_adversary_levels(adversary_id)
            level_options = [
                ft.dropdown.Option(level.level, level.level) for level in levels
            ]
            adversary_level = ft.Dropdown(
                label="Nivel del adversario",
                options=level_options,
                disabled=not bool(level_options),
            )
            difficulty_text = ft.Text("Dificultad: —")

            def update_difficulty(event: ft.ControlEvent | None = None) -> None:
                logger.debug(
                    "Updating difficulty adversary_id=%s level=%s",
                    adversary_id,
                    adversary_level.value,
                )
                difficulty_value = get_adversary_difficulty(
                    adversary_id, adversary_level.value
                )
                difficulty_text.value = (
                    f"Dificultad: {difficulty_value}"
                    if difficulty_value is not None
                    else "Dificultad: —"
                )
                page.update()

            adversary_level.on_change = update_difficulty
            update_difficulty()

            def handle_start(event: ft.ControlEvent) -> None:
                logger.info(
                    "Start incursion requested era_id=%s period_id=%s incursion_id=%s",
                    era_id,
                    period_id,
                    incursion_id,
                )
                if not period_adversaries_assigned:
                    logger.warning("Cannot start incursion; adversaries not assigned")
                    show_message("Debes asignar adversarios del periodo.")
                    return
                if not adversary_id:
                    logger.warning("Cannot start incursion; adversary not selected")
                    show_message("Debes asignar un adversario.")
                    return
                difficulty_value = get_adversary_difficulty(
                    adversary_id, adversary_level.value
                )
                if not adversary_level.value or difficulty_value is None:
                    logger.warning("Cannot start incursion; invalid adversary level")
                    show_message("Debes seleccionar un nivel válido.")
                    return
                try:
                    service.start_incursion(
                        era_id,
                        period_id,
                        incursion_id,
                        adversary_level.value,
                        difficulty_value,
                    )
                except ValueError as exc:
                    logger.error(
                        "Failed to start incursion error=%s", exc, exc_info=True
                    )
                    show_message(str(exc))
                    return
                load_detail()
                page.update()
                logger.info("Incursion started incursion_id=%s", incursion_id)

            actions_section.content = ft.Column(
                [
                    ft.Text("Acciones principales", weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(
                        "Selecciona el nivel y confirma el inicio de la incursión.",
                        size=12,
                        color=ft.Colors.BLUE_GREY_400,
                    ),
                    ft.Text(
                        f"Adversario: {adversary_name}",
                        size=12,
                        color=ft.Colors.BLUE_GREY_500,
                    ),
                    adversary_level,
                    difficulty_text,
                    ft.ElevatedButton(
                        "Iniciar incursión",
                        icon=ft.Icons.PLAY_ARROW,
                        on_click=handle_start,
                    ),
                ],
                spacing=8,
            )

        if incursion.get("started_at") and not incursion.get("ended_at"):

            def handle_pause(event: ft.ControlEvent) -> None:
                logger.info("Pause session clicked incursion_id=%s", incursion_id)
                service.pause_incursion(era_id, period_id, incursion_id)
                load_detail()
                page.update()
                logger.debug("Session paused incursion_id=%s", incursion_id)

            def handle_resume(event: ft.ControlEvent) -> None:
                logger.info("Resume session clicked incursion_id=%s", incursion_id)
                service.resume_incursion(era_id, period_id, incursion_id)
                load_detail()
                page.update()
                logger.debug("Session resumed incursion_id=%s", incursion_id)
            actions_section.content = ft.Column(
                [
                    ft.Text("Acciones principales", weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(
                        "La incursión está activa. Puedes reanudar o pausar la sesión.",
                        size=12,
                        color=ft.Colors.BLUE_GREY_400,
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Reanudar incursión",
                                icon=ft.Icons.PLAY_ARROW,
                                on_click=handle_resume,
                            ),
                            ft.TextButton(
                                "Pausar sesión",
                                icon=ft.Icons.PAUSE,
                                on_click=handle_pause if open_session else handle_resume,
                            ),
                        ],
                        spacing=12,
                        wrap=True,
                    ),
                ],
                spacing=8,
            )

        if not actions_section.content:
            actions_section.content = ft.Column(
                [
                    ft.Text("Acciones principales", weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(
                        "La incursión está finalizada. Vista solo lectura.",
                        size=12,
                        color=ft.Colors.BLUE_GREY_400,
                    ),
                ],
                spacing=8,
            )

        sessions_list = ft.ListView(spacing=6, expand=False)
        if not sessions:
            sessions_list.controls.append(ft.Text("No hay sesiones registradas."))
        else:
            for session in sessions:
                sessions_list.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.TIMER),
                        title=ft.Text(
                            f"{format_ts(session.get('started_at'))} → {format_ts(session.get('ended_at'))}"
                        ),
                    )
                )
        sessions_section.content = ft.Column(
            [
                ft.Text("Sesiones registradas", weight=ft.FontWeight.BOLD, size=16),
                sessions_list,
                ft.Text(f"Duración total: {total_minutes(sessions)} min"),
            ],
            spacing=8,
        )

        def handle_finalize(
            dialog: ft.AlertDialog, fields: dict[str, ft.TextField]
        ) -> None:
            logger.info(
                "Finalize incursion requested incursion_id=%s result=%s",
                incursion_id,
                fields["result"].value,
            )
            if not fields["result"].value:
                logger.warning("Finalize blocked; missing result incursion_id=%s", incursion_id)
                show_message("Debes indicar el resultado.")
                return
            try:
                service.finalize_incursion(
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
                show_message("Revisa los valores numéricos.")
                return
            dialog.open = False
            load_detail()
            page.update()
            logger.info("Incursion finalized incursion_id=%s", incursion_id)

        def open_finalize_dialog(event: ft.ControlEvent) -> None:
            logger.info("Opening finalize dialog incursion_id=%s", incursion_id)
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
                "invader_cards_remaining": ft.TextField(
                    label="Cartas invasoras restantes",
                    keyboard_type=ft.KeyboardType.NUMBER,
                ),
                "invader_cards_out_of_deck": ft.TextField(
                    label="Cartas invasoras fuera del mazo",
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
            }

            def handle_cancel_click(event: ft.ControlEvent) -> None:
                logger.info("Finalize dialog cancelled incursion_id=%s", incursion_id)
                close_dialog(dialog)

            def handle_save_click(event: ft.ControlEvent) -> None:
                handle_finalize(dialog, fields)

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Finalizar incursión"),
                content=ft.Column(
                    list(fields.values()), tight=True, scroll=ft.ScrollMode.AUTO
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=handle_cancel_click),
                    ft.ElevatedButton(
                        "Guardar",
                        on_click=handle_save_click,
                    ),
                ],
            )
            page.dialog = dialog
            dialog.open = True
            page.update()
            logger.debug("Finalize dialog opened incursion_id=%s", incursion_id)

        if incursion.get("ended_at"):
            result_value = incursion.get("result")
            result_label = "Victoria" if result_value == "win" else "Derrota"
            result_section.content = ft.Column(
                [
                    ft.Text("Resultado final", weight=ft.FontWeight.BOLD, size=16),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.EMOJI_EVENTS),
                        title=ft.Text(result_label),
                        subtitle=ft.Text(
                            f"Score {incursion.get('score')}"
                        ),
                    ),
                ],
                spacing=8,
            )
        elif incursion.get("started_at"):
            result_section.content = ft.Column(
                [
                    ft.Text("Finalización", weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(
                        "Completa los datos para cerrar la incursión."
                    ),
                    ft.ElevatedButton(
                        "Finalizar incursión",
                        icon=ft.Icons.FLAG,
                        on_click=open_finalize_dialog,
                    ),
                ],
                spacing=8,
            )
        else:
            result_section.content = ft.Column(
                [
                    ft.Text("Resultado", weight=ft.FontWeight.BOLD, size=16),
                    ft.Text("La incursión aún no ha comenzado."),
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
                        header_container,
                        board_placeholder,
                        data_section,
                        actions_section,
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
