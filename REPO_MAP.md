# REPO_MAP

## Arbol de carpetas (max. 3 niveles)

```text
.
|- .env
|- .git/
|- .gitignore
|- DOCUMENTATION.md
|- instructions.txt
|- Pipfile
|- Pipfile.lock
|- README.md
|- STATUS.md
|- app/
|  |- __init__.py
|  |- main.py
|  |- assets/
|  |  |- layouts/
|  |- screens/
|  |  |- __init__.py
|  |  |- data_lookup.py
|  |  |- shared_components.py
|  |  |- eras/
|  |  |- incursion_detail/
|  |  |- incursions/
|  |  |- periods/
|  |- services/
|  |  |- __init__.py
|  |  |- firestore_service.py
|  |  |- score_service.py
|  |- utils/
|     |- __init__.py
|     |- datetime_format.py
|     |- logger.py
|     |- navigation.py
|- logs/
|- pc/
|  |- data/
|  |  |- input/
|  |  |- output/
|  |- legacy/
|  |  |- data/
|  |  |- data_loader.py
|  |  |- generar_campana.py
|  |  |- generar_jornadas_espiritus.py
|  |- firestore_service.py
|  |- firestore_test.py
|- tests/
|  |- manual_firestore_checks.py
```

## Pantallas Flet (screen files)

### `app/screens/eras/eras_screen.py`

- Proposito: muestra la lista de `era` con su estado (`is_active`) y si hay `active_incursion`.
- Lee: `FirestoreService.list_eras()` y `FirestoreService.get_active_incursion()` (via `get_active_incursion`).
- Acciones: boton "Ver periodos" -> `go_to("/eras/{era_id}")`; boton "Ir a incursion activa" -> `go_to("/eras/{era_id}/periods/{period_id}/incursions/{incursion_id}")` si existe.
- Llama a: `eras_components.era_card`, `eras_state.get_era_status`, `eras_state.get_incursion_status`, `eras_handlers.build_open_periods_handler`, `eras_handlers.build_open_active_handler`.

### `app/screens/periods/periods_screen.py`

- Proposito: lista periodos de una era y decide la accion UI segun `revealed_at`, `adversaries_assigned_at`, `ended_at`.
- Lee: `FirestoreService.list_periods()`, `FirestoreService.list_incursions()`, `data_lookup.get_adversary_catalog()`, `data_lookup.get_spirit_name()`.
- Acciones: abrir periodo (`go_to`), abrir dialogo de asignacion de adversarios, guardar asignaciones, revelar periodo.
- Llama a: `periods_handlers.assign_period_adversaries`, `periods_handlers.reveal_period`, `periods_handlers.close_dialog`, `periods_state.get_period_action`, `periods_state.can_reveal`, `periods_components.period_card`, `periods_components.incursions_preview`.

### `app/screens/incursions/incursions_screen.py`

- Proposito: lista incursiones de un periodo con detalles de spirits/boards/layout/adversary y su estado.
- Lee: `incursions_handlers.list_incursions()` -> `FirestoreService.list_incursions()` y campos `spirit_1_id`, `spirit_2_id`, `board_1`, `board_2`, `board_layout`, `adversary_id`, `ended_at`, `result`, `is_active`.
- Acciones: boton "Abrir" navega al detalle de la incursion.
- Llama a: `incursions_state.get_spirit_info`, `get_board_info`, `get_layout_info`, `get_adversary_info`, `get_incursion_status`, `incursions_components.incursion_card`, `incursions_handlers.build_open_incursion_handler`.

### `app/screens/incursion_detail/incursion_detail_screen.py`

- Proposito: detalle completo de una incursion; gestion de sesiones (`sessions`), `adversary_level`/`difficulty` y finalizacion con `score`.
- Lee: `get_incursion()` (usa `FirestoreService.list_incursions()`), `get_period()` (usa `FirestoreService.list_periods()`), `list_sessions()` (usa `FirestoreService.list_sessions()`), `data_lookup.get_*`.
- Acciones: actualizar `adversary_level`/`difficulty`, iniciar/finalizar sesion, finalizar incursion con formulario y preview de score/tiempo.
- Llama a: `incursion_detail_handlers.update_adversary_level/start_session/end_session/finalize_incursion`, `incursion_detail_state.resolve_session_state/can_edit_adversary_level/compute_score_preview`, `incursion_detail_components.dark_section/light_section`.

## Modulos core (services, state/helpers, navigation)

### services

- `app/services/firestore_service.py` — acceso a Firestore para `eras`, `periods`, `incursions`, `sessions`, control de `active_incursion_id`, reglas de negocio y validaciones.
- `app/services/score_service.py` — calculo de `score` con `result`, `difficulty` y metricas del cierre.

### state/helpers

- `app/screens/data_lookup.py` — carga TSV desde `pc/data/input` y resuelve nombres/niveles/dificultad (ej. `get_spirit_name`, `get_adversary_levels`).
- `app/screens/shared_components.py` — UI comun (`header_text`, `status_chip`, `section_card`, `action_button`).
- `app/screens/eras/eras_state.py` — estado/colores de era e incursion.
- `app/screens/periods/periods_state.py` — reglas de accion de periodo (`can_reveal`, `get_period_action`).
- `app/screens/incursions/incursions_state.py` — estado de incursion y textos agregados.
- `app/screens/incursion_detail/incursion_detail_state.py` — estado de sesion, reglas de edicion, formulas de score.
- `app/screens/eras/eras_components.py` — `era_card`.
- `app/screens/periods/periods_components.py` — `period_card`, `incursions_preview`.
- `app/screens/incursions/incursions_components.py` — `incursion_card`.
- `app/screens/incursion_detail/incursion_detail_components.py` — `dark_section`, `light_section`, `summary_tile`.
- `app/screens/eras/eras_handlers.py` — handlers de navegacion y carga (`build_open_periods_handler`, `build_open_active_handler`).
- `app/screens/periods/periods_handlers.py` — handlers de dialogo/acciones (`assign_period_adversaries`, `reveal_period`).
- `app/screens/incursions/incursions_handlers.py` — handlers de navegacion y listado (`build_open_incursion_handler`, `list_incursions`).
- `app/screens/incursion_detail/incursion_detail_handlers.py` — handlers de Firestore (`get_incursion`, `list_sessions`, `start_session`, `end_session`, `finalize_incursion`, `update_adversary_level`) y UI (`show_message`).
- `app/utils/datetime_format.py` — parseo/normalizacion UTC y formato local para UI.
- `app/utils/logger.py` — configuracion de logging a `logs/`.

### navigation

- `app/utils/navigation.py` — helpers `go` y `go_to` para routing.
- `app/main.py` — wiring de rutas y construccion de `ft.View` segun `/eras/.../periods/.../incursions/...`.

## Invariantes/validaciones

- `app/services/firestore_service.py` `reveal_period()` — exige que el `period` exista, que el periodo previo tenga `ended_at` (si no es el primero) y que `revealed_at` no este definido.
- `app/services/firestore_service.py` `set_incursion_adversary()` — requiere `period` existente, `revealed_at` presente, no `ended_at`, no `adversaries_assigned_at`, y `incursion` existente.
- `app/services/firestore_service.py` `assign_period_adversaries()` — valida periodo revelado/no finalizado/no asignado, exactamente 4 incursiones, claves de `assignments` = IDs de incursion, todos los `adversary_id` presentes y sin duplicados.
- `app/services/firestore_service.py` `start_session()` — valida periodo revelado/no finalizado/con `adversaries_assigned_at`, no otra `active_incursion_id` en la era, `incursion` existente y no finalizada, sin sesiones abiertas; si es primera sesion: `adversary_level` y `difficulty` presentes y adversarios unicos en el periodo.
- `app/services/firestore_service.py` `_parse_active_incursion_id()` — formato `"{period_id}::{incursion_id}"` y partes no vacias.
- `app/services/firestore_service.py` `finalize_incursion()` — bloquea si `ended_at` ya existe; al finalizar limpia `active_incursion_id` y puede escribir `periods.ended_at` si `_period_complete()` es True.
- `app/screens/periods/periods_state.py` `can_reveal()` — solo permite revelar si el periodo anterior tiene `ended_at`.
- `app/screens/incursion_detail/incursion_detail_state.py` `can_edit_adversary_level()` — solo permite editar si no hay `ended_at` y aun no hay sesiones.
- `app/screens/incursion_detail/incursion_detail_screen.py` `handle_session_action()` — requiere `adversary_level` y `difficulty` antes de `start_session`; bloquea accion si `SESSION_STATE_FINALIZED`.
- `app/screens/incursion_detail/incursion_detail_screen.py` `handle_finalize_inline()` — requiere `result`, cierra sesion abierta antes de `finalize_incursion`; `ValueError` -> mensaje.
- `app/screens/data_lookup.py` `_load_tsv_rows()` — exige archivo existente y headers con campos requeridos; descarta filas incompletas.
- Otros invariantes no visibles en el repo revisado: desconocido.

## Seccion especifica: `app/screens/incursion_detail/incursion_detail_screen.py`

### Flujo (iniciar/pausar/reanudar/finalizar)

- Iniciar sesion: si `state == SESSION_STATE_NOT_STARTED` y no hay `open_session`, `handle_session_action()` valida `adversary_level` + `difficulty` y llama a `start_session()`.
- Pausar/finalizar sesion: si `open_session` es True, `handle_session_action()` llama a `end_session()` y recarga detalle.
- Reanudar: si hay sesiones previas pero no abiertas (`state == SESSION_STATE_BETWEEN_SESSIONS`), `handle_session_action()` vuelve a llamar a `start_session()` (crea una nueva sesion).
- Finalizar incursion: `handle_finalize_inline()` exige `result`, cierra sesion abierta si existe, y ejecuta `finalize_incursion()`; el estado pasa a `SESSION_STATE_FINALIZED`.

### Firestore (lecturas/writes)

- Lecturas: `get_incursion()` -> `FirestoreService.list_incursions()` (campos usados: `spirit_1_id`, `spirit_2_id`, `board_1`, `board_2`, `board_layout`, `adversary_id`, `adversary_level`, `difficulty`, `result`, `ended_at`, `is_active`, `score`, `player_count`, `dahan_alive`, `blight_on_island`, `invader_cards_remaining`, `invader_cards_out_of_deck`); `get_period()` -> `FirestoreService.list_periods()` (campos `index`, `adversaries_assigned_at`); `list_sessions()` -> `FirestoreService.list_sessions()` (campos `started_at`, `ended_at`).
- Escrituras: `update_adversary_level()` -> `update_incursion_adversary_level()` (actualiza `adversary_level`, `difficulty`, opcional `adversary_id`); `start_session()` -> `start_session()` (marca `incursion.is_active`, puede setear `incursion.started_at`, crea doc en `sessions`, actualiza `eras.active_incursion_id` y `active_incursion`); `end_session()` -> `end_session()` (setea `sessions.ended_at`); `finalize_incursion()` -> `finalize_incursion()` (actualiza `incursion` con `ended_at`, `result`, `player_count`, `invader_cards_remaining`, `invader_cards_out_of_deck`, `dahan_alive`, `blight_on_island`, `score`, `is_active`, limpia `eras.active_incursion_id`/`active_incursion`, y puede actualizar `periods.ended_at`).

### Dependencias (state/handlers/services)

- `app/screens/incursion_detail/incursion_detail_handlers.py` — lectura/escritura Firestore y mensajes UI (`show_message`).
- `app/screens/incursion_detail/incursion_detail_state.py` — `resolve_session_state`, `can_edit_adversary_level`, `compute_score_preview`, `get_result_label`, `get_score_formula`.
- `app/screens/incursion_detail/incursion_detail_components.py` — `dark_section`, `light_section`.
- `app/screens/data_lookup.py` — `get_spirit_name`, `get_board_name`, `get_layout_name`, `get_adversary_name`, `get_adversary_levels`, `get_adversary_difficulty`.
- `app/services/firestore_service.py` — persistencia y validaciones.
- `app/utils/datetime_format.py` — `format_datetime_local` para sesiones.

### UI contract (no cambiar)

- `ft.AppBar` con titulo "Incursion" y `center_title=True`.
- Contenedor principal: `ft.Container` con `padding=16`, `scroll=ft.ScrollMode.AUTO`, `expand=True`, y `ft.Column([setup_section, bottom_section], spacing=16)`.
- `setup_section` usa `dark_section` (padding 20, border_radius 20, `bgcolor=ft.Colors.BLUE_GREY_900`).
- Orden interno de `setup_section`: texto pequeno con "Incursion {index} · {period_label}" -> fila con spirits/boards -> texto de `layout_name` -> placeholder de layout (`height=140`, `width=240`, `bgcolor=ft.Colors.BLUE_GREY_700`, `border_radius=12`) -> `ft.Divider` -> `adversary_level_block`.
- `adversary_level_block` es un `ft.Container` centrado con `bgcolor=ft.Colors.BLUE_GREY_50`, `border_radius=8` y muestra `adversary_name` + selector o texto con "Nivel ... · Dificultad ..." en la misma linea.
- `bottom_section` usa `light_section` (padding 16, border_radius 16, borde gris, fondo blanco).
- Orden en `bottom_section`: `time_text` grande con prefijo de reloj (emoji) -> columna con boton principal `ft.FilledButton` (`width=320`, `height=52`, `bgcolor=ft.Colors.BLUE_700`) -> `result_summary` (si finalizado) -> `finalize_panel` -> `sessions_detail`.
- `finalize_panel` es `ft.Card` con titulo "Finalizar incursion", filas de inputs (result/player_count, dahan_alive/blight_on_island, invader_cards_remaining/invader_cards_out_of_deck), preview de formula/puntuacion y fila de confirmacion (`confirm_row`) integrada.
