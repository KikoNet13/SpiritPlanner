from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

import flet as ft

from app.services.firestore_service import FirestoreService
from app.screens.data_lookup import (
    get_adversary_catalog,
    get_adversary_difficulty,
    get_adversary_levels,
    get_adversary_name,
    get_board_name,
    get_layout_name,
    get_spirit_name,
)


def incursion_detail_view(
    page: ft.Page,
    service: FirestoreService,
    era_id: str,
    period_id: str,
    incursion_id: str,
) -> ft.Control:
    title = ft.Text("Detalle de incursión", size=22, weight=ft.FontWeight.BOLD)
    header_container = ft.Container(
        padding=12,
        border=ft.border.all(1, ft.Colors.GREY_300),
        border_radius=12,
    )
    setup_column = ft.ListView(spacing=12, expand=True)
    sessions_column = ft.ListView(spacing=12, expand=True)
    result_column = ft.ListView(spacing=12, expand=True)

    def status_chip(label: str, color: str) -> ft.Container:
        return ft.Container(
            content=ft.Text(label, size=12, color=ft.Colors.WHITE),
            bgcolor=color,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=12,
        )

    def format_ts(value: datetime | None) -> str:
        if not value:
            return "—"
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def total_minutes(sessions: list[dict]) -> int:
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
        page.snack_bar = ft.SnackBar(ft.Text(text))
        page.snack_bar.open = True
        page.update()

    def close_dialog(dialog: ft.AlertDialog) -> None:
        dialog.open = False
        page.update()

    def open_adversary_selector(
        incursion: dict, on_select: Callable[[str], None]
    ) -> None:
        spirit_info = (
            f"{get_spirit_name(incursion.get('spirit_1_id'))} / "
            f"{get_spirit_name(incursion.get('spirit_2_id'))}"
        )
        options = sorted(
            get_adversary_catalog().values(), key=lambda item: item.name
        )
        list_view = ft.ListView(spacing=8, expand=True)

        def handle_select(adversary_id: str) -> None:
            on_select(adversary_id)
            close_dialog(dialog)

        for option in options:
            list_view.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.icons.SHIELD),
                    title=ft.Text(option.name),
                    on_click=lambda event, aid=option.adversary_id: handle_select(
                        aid
                    ),
                )
            )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Seleccionar adversario"),
            content=ft.Column(
                [
                    ft.Text(f"Espíritus: {spirit_info}"),
                    list_view,
                ],
                tight=True,
                spacing=12,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda event: close_dialog(dialog))
            ],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def update_adversary(
        incursion: dict, adversary_id: str, label: ft.Text
    ) -> None:
        try:
            service.set_incursion_adversary(
                era_id, period_id, incursion["id"], adversary_id
            )
        except ValueError as exc:
            show_message(str(exc))
            return
        label.value = get_adversary_name(adversary_id)
        load_detail()

    def load_detail() -> None:
        setup_column.controls.clear()
        sessions_column.controls.clear()
        result_column.controls.clear()

        incursions = service.list_incursions(era_id, period_id)
        incursion = next(
            (item for item in incursions if item["id"] == incursion_id), None
        )
        if not incursion:
            setup_column.controls.append(ft.Text("Incursión no encontrada."))
            page.update()
            return
        period = next(
            (item for item in service.list_periods(era_id) if item["id"] == period_id),
            None,
        )
        period_started = bool(period and period.get("started_at"))

        sessions = service.list_sessions(era_id, period_id, incursion_id)
        open_session = any(session.get("ended_at") is None for session in sessions)

        status = "No iniciado"
        status_color = ft.Colors.GREY_500
        if incursion.get("ended_at"):
            status = "Finalizado"
            status_color = ft.Colors.BLUE_600
        elif incursion.get("started_at"):
            status = "Activo"
            status_color = ft.Colors.GREEN_600

        header_container.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(
                            f"Incursión {incursion.get('index', 0)}",
                            weight=ft.FontWeight.BOLD,
                            size=16,
                        ),
                        status_chip(status, status_color),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text(f"Inicio: {format_ts(incursion.get('started_at'))}"),
                ft.Text(f"Fin: {format_ts(incursion.get('ended_at'))}"),
            ],
            spacing=6,
        )

        setup_column.controls.append(
            ft.ListTile(
                leading=ft.Icon(ft.icons.GROUP),
                title=ft.Text("Espíritus"),
                subtitle=ft.Text(
                    f"{get_spirit_name(incursion.get('spirit_1_id'))} / "
                    f"{get_spirit_name(incursion.get('spirit_2_id'))}"
                ),
            )
        )
        setup_column.controls.append(
            ft.ListTile(
                leading=ft.Icon(ft.icons.DASHBOARD),
                title=ft.Text("Tableros"),
                subtitle=ft.Text(
                    f"{get_board_name(incursion.get('board_1'))} + "
                    f"{get_board_name(incursion.get('board_2'))}"
                ),
            )
        )
        setup_column.controls.append(
            ft.ListTile(
                leading=ft.Icon(ft.icons.VIEW_QUILT),
                title=ft.Text("Distribución"),
                subtitle=ft.Text(get_layout_name(incursion.get("board_layout"))),
            )
        )

        adversary_label = ft.Text(
            get_adversary_name(incursion.get("adversary_id"))
        )
        strategy_section = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.SHIELD),
                            ft.Text("Adversario", weight=ft.FontWeight.BOLD),
                        ],
                        spacing=8,
                    ),
                    ft.Row(
                        [ft.Text("Selección:"), adversary_label],
                        spacing=6,
                        wrap=True,
                    ),
                    ft.Text(
                        f"Nivel: {incursion.get('adversary_level', '—')}"
                    ),
                    ft.Text(
                        f"Dificultad: {incursion.get('difficulty') if incursion.get('difficulty') is not None else '—'}"
                    ),
                ],
                spacing=6,
            ),
            padding=12,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=12,
        )
        setup_column.controls.append(strategy_section)

        if not incursion.get("started_at") and not period_started:
            setup_column.controls.append(
                ft.OutlinedButton(
                    "Elegir adversario",
                    icon=ft.icons.EDIT,
                    on_click=lambda event: open_adversary_selector(
                        incursion,
                        lambda adversary_id: update_adversary(
                            incursion, adversary_id, adversary_label
                        ),
                    ),
                )
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
                if not adversary_id:
                    show_message("Debes asignar un adversario.")
                    return
                difficulty_value = get_adversary_difficulty(
                    adversary_id, adversary_level.value
                )
                if not adversary_level.value or difficulty_value is None:
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
                    show_message(str(exc))
                    return
                load_detail()
                page.update()

            setup_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Inicio de incursión",
                                weight=ft.FontWeight.BOLD,
                            ),
                            adversary_level,
                            difficulty_text,
                            ft.ElevatedButton(
                                "Iniciar incursión", on_click=handle_start
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=12,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=12,
                )
            )

        if incursion.get("started_at") and not incursion.get("ended_at"):

            def handle_pause(event: ft.ControlEvent) -> None:
                service.pause_incursion(era_id, period_id, incursion_id)
                load_detail()
                page.update()

            def handle_resume(event: ft.ControlEvent) -> None:
                service.resume_incursion(era_id, period_id, incursion_id)
                load_detail()
                page.update()

            sessions_column.controls.append(
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "Pausar sesión" if open_session else "Reanudar sesión",
                            icon=ft.icons.PAUSE if open_session else ft.icons.PLAY_ARROW,
                            on_click=handle_pause if open_session else handle_resume,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                )
            )

        sessions_column.controls.append(
            ft.Text("Sesiones registradas", weight=ft.FontWeight.BOLD)
        )
        sessions_list = ft.ListView(spacing=6, expand=False)
        if not sessions:
            sessions_list.controls.append(ft.Text("No hay sesiones registradas."))
        else:
            for session in sessions:
                sessions_list.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.TIMER),
                        title=ft.Text(
                            f"{format_ts(session.get('started_at'))} → {format_ts(session.get('ended_at'))}"
                        ),
                    )
                )
        sessions_column.controls.append(sessions_list)
        sessions_column.controls.append(
            ft.Text(f"Duración total: {total_minutes(sessions)} min")
        )

        def handle_finalize(
            dialog: ft.AlertDialog, fields: dict[str, ft.TextField]
        ) -> None:
            if not fields["result"].value:
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
                show_message("Revisa los valores numéricos.")
                return
            dialog.open = False
            load_detail()
            page.update()

        def open_finalize_dialog(event: ft.ControlEvent) -> None:
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
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Finalizar incursión"),
                content=ft.Column(
                    list(fields.values()), tight=True, scroll=ft.ScrollMode.AUTO
                ),
                actions=[
                    ft.TextButton(
                        "Cancelar", on_click=lambda event: close_dialog(dialog)
                    ),
                    ft.ElevatedButton(
                        "Guardar",
                        on_click=lambda event: handle_finalize(dialog, fields),
                    ),
                ],
            )
            page.dialog = dialog
            dialog.open = True
            page.update()

        if incursion.get("ended_at"):
            result_value = incursion.get("result")
            result_label = "Victoria" if result_value == "win" else "Derrota"
            result_column.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.icons.EMOJI_EVENTS),
                    title=ft.Text("Resultado final"),
                    subtitle=ft.Text(
                        f"{result_label} · Score {incursion.get('score')}"
                    ),
                )
            )
        elif incursion.get("started_at"):
            result_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "Finalización",
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "Completa los datos para cerrar la incursión."
                            ),
                            ft.ElevatedButton(
                                "Finalizar incursión",
                                icon=ft.icons.FLAG,
                                on_click=open_finalize_dialog,
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=12,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=12,
                )
            )
        else:
            result_column.controls.append(
                ft.Text("La incursión aún no ha comenzado.")
            )

        page.update()

    load_detail()

    return ft.Column(
        [
            ft.AppBar(title=ft.Text("Incursión"), center_title=True),
            ft.Container(
                content=ft.Column(
                    [
                        title,
                        header_container,
                        ft.Tabs(
                            expand=True,
                            animation_duration=200,
                            tabs=[
                                ft.Tab(text="Configuración", content=setup_column),
                                ft.Tab(text="Sesiones", content=sessions_column),
                                ft.Tab(text="Resultado", content=result_column),
                            ],
                        ),
                    ],
                    expand=True,
                    spacing=12,
                ),
                padding=16,
                expand=True,
            ),
        ],
        expand=True,
        spacing=0,
    )
