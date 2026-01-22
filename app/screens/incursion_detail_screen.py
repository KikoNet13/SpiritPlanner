from __future__ import annotations

from datetime import datetime, timezone

import flet as ft

from app.services.firestore_service import FirestoreService
from app.services.score_service import calculate_score


def incursion_detail_view(
    page: ft.Page,
    service: FirestoreService,
    era_id: str,
    period_id: str,
    incursion_id: str,
) -> ft.View:
    title = ft.Text("Detalle de incursión", size=22, weight=ft.FontWeight.BOLD)
    content_column = ft.Column(spacing=10)
    sessions_column = ft.Column(spacing=6)

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

    def load_detail() -> None:
        content_column.controls.clear()
        sessions_column.controls.clear()

        incursions = service.list_incursions(era_id, period_id)
        incursion = next(
            (item for item in incursions if item["id"] == incursion_id), None
        )
        if not incursion:
            content_column.controls.append(ft.Text("Incursión no encontrada."))
            page.update()
            return

        sessions = service.list_sessions(era_id, period_id, incursion_id)
        open_session = any(session.get("ended_at") is None for session in sessions)

        content_column.controls.append(
            ft.Text(
                f"Incursión {incursion.get('index', 0)}",
                weight=ft.FontWeight.BOLD,
            )
        )
        content_column.controls.append(
            ft.Text(
                f"Espíritus: {incursion.get('spirit_1_id', '')} / {incursion.get('spirit_2_id', '')}"
            )
        )
        content_column.controls.append(
            ft.Text(
                f"Tableros: {incursion.get('board_1', '')} + {incursion.get('board_2', '')}"
            )
        )
        content_column.controls.append(
            ft.Text(f"Adversario: {incursion.get('adversary_id', '—')}")
        )
        content_column.controls.append(
            ft.Text(f"Inicio: {format_ts(incursion.get('started_at'))}")
        )
        content_column.controls.append(
            ft.Text(f"Fin: {format_ts(incursion.get('ended_at'))}")
        )
        status = "No iniciado"
        if incursion.get("ended_at"):
            status = "Finalizado"
        elif incursion.get("started_at"):
            status = "Activo"
        content_column.controls.append(ft.Text(f"Estado: {status}"))

        if incursion.get("ended_at"):
            score = incursion.get("score")
            result = incursion.get("result")
            content_column.controls.append(ft.Text(f"Resultado: {result}"))
            content_column.controls.append(ft.Text(f"Score: {score}"))

        if not incursion.get("started_at"):
            adversary_level = ft.TextField(label="Nivel del adversario")
            difficulty = ft.TextField(
                label="Dificultad", keyboard_type=ft.KeyboardType.NUMBER
            )

            def handle_start(event: ft.ControlEvent) -> None:
                if not adversary_level.value or not difficulty.value:
                    show_message("Debes completar nivel y dificultad.")
                    return
                try:
                    service.start_incursion(
                        era_id,
                        period_id,
                        incursion_id,
                        adversary_level.value,
                        int(difficulty.value),
                    )
                except ValueError as exc:
                    show_message(str(exc))
                    return
                load_detail()
                page.update()

            content_column.controls.append(adversary_level)
            content_column.controls.append(difficulty)
            content_column.controls.append(
                ft.ElevatedButton("Iniciar incursión", on_click=handle_start)
            )
        elif not incursion.get("ended_at"):

            def handle_pause(event: ft.ControlEvent) -> None:
                service.pause_incursion(era_id, period_id, incursion_id)
                load_detail()
                page.update()

            def handle_resume(event: ft.ControlEvent) -> None:
                service.resume_incursion(era_id, period_id, incursion_id)
                load_detail()
                page.update()

            def close_dialog(dialog: ft.AlertDialog) -> None:
                dialog.open = False
                page.update()

            def handle_finalize(
                dialog: ft.AlertDialog, fields: dict[str, ft.TextField]
            ) -> None:
                if not fields["result"].value:
                    show_message("Debes indicar el resultado.")
                    return
                try:
                    score = calculate_score(
                        difficulty=int(incursion.get("difficulty", 0)),
                        result=fields["result"].value,
                        invader_cards_remaining=int(
                            fields["invader_cards_remaining"].value or 0
                        ),
                        invader_cards_out_of_deck=int(
                            fields["invader_cards_out_of_deck"].value or 0
                        ),
                        player_count=int(fields["player_count"].value or 2),
                        dahan_alive=int(fields["dahan_alive"].value or 0),
                        blight_on_island=int(fields["blight_on_island"].value or 0),
                    )
                except ValueError:
                    show_message("Revisa los valores numéricos.")
                    return

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
                    score=score,
                )
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

            if open_session:
                content_column.controls.append(
                    ft.ElevatedButton("Pausar sesión", on_click=handle_pause)
                )
            else:
                content_column.controls.append(
                    ft.ElevatedButton("Reanudar sesión", on_click=handle_resume)
                )
            content_column.controls.append(
                ft.OutlinedButton("Finalizar incursión", on_click=open_finalize_dialog)
            )

        sessions_column.controls.append(ft.Text("Sesiones", weight=ft.FontWeight.BOLD))
        if not sessions:
            sessions_column.controls.append(ft.Text("No hay sesiones registradas."))
        else:
            for session in sessions:
                sessions_column.controls.append(
                    ft.Text(
                        f"{format_ts(session.get('started_at'))} → {format_ts(session.get('ended_at'))}"
                    )
                )
        sessions_column.controls.append(
            ft.Text(f"Duración total: {total_minutes(sessions)} min")
        )
        page.update()

    load_detail()

    return ft.View(
        route=f"/eras/{era_id}/periods/{period_id}/incursions/{incursion_id}",
        controls=[
            ft.AppBar(title=ft.Text("Incursión")),
            ft.Container(
                content=ft.Column(
                    [
                        title,
                        content_column,
                        sessions_column,
                    ],
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=16,
            ),
        ],
    )
