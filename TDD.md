# TDD - SpiritPlanner (CANONICO)

Este documento describe el sistema real segun REPO_MAP.md y el codigo actual.
Si algo no es visible en el codigo, se marca como "desconocido / por confirmar".

## Fuentes de verdad

1) TDD.md (este documento)
2) adr/
3) Codigo del repo (implementacion)

Docs no canonicos: README.md, STATUS.md, DOCUMENTATION.md, FLET_NOTES.md.

## Alcance

- Gestion de Eras, Periodos, Incursions y Sessions en Firestore.
- UI Flet para consultar y operar el flujo de juego.
- Scripts PC para generar una Era desde TSV.
- Export TSV: ver seccion especifica.

Fuera de alcance: features no visibles en el codigo actual.

## Arquitectura (alto nivel)

- UI: `app/` (Flet) con MVVM declarativo:
  - `*_model.py`: dataclasses de dominio/DTO para la vista.
  - `*_viewmodel.py`: ViewModels `@ft.observable` con estado puro (sin `page`).
  - `*_view.py`: componentes `@ft.component` con hooks y efectos UI via `ft.use_effect`.
  - `ft.use_state` crea el ViewModel sin lambdas: `vm, _ = ft.use_state(MyViewModel())`.
  - `FirestoreService` se inyecta via `page.session` y se pasa a metodos explicitos del ViewModel.
- Persistencia: Firestore via `app/services/firestore_service.py`.
- Scripts PC: `pc/generate_era.py`, `pc/firestore_service.py`.
- Catalogos: TSV en `pc/data/input`.

## Routing (vigente)

- `/eras`
- `/eras/{era_id}`
- `/eras/{era_id}/periods/{period_id}`
- `/eras/{era_id}/periods/{period_id}/incursions/{incursion_id}`

## Modelo de datos (Firestore)

### Colecciones

```text
eras/{era_id}
  periods/{period_id}
    incursions/{incursion_id}
      sessions/{session_id}
```

### Era (eras/{era_id})

Campos observados:

- `is_active` (bool) (usado en UI).
- `created_at` (timestamp, set por PC).
- `active_incursion_id` (string, formato "{period_id}::{incursion_id}").
- `active_incursion` (object con `period_id`, `incursion_id`).

Desconocido / por confirmar:

- Ciclo de vida de `is_active` fuera de la creacion.
- Uso real de `active_incursion` (no se lee en app).

### Period (periods/{period_id})

Campos observados:

- `index` (int).
- `created_at` (timestamp, set por PC).
- `revealed_at` (timestamp | null).
- `adversaries_assigned_at` (timestamp | null).
- `ended_at` (timestamp | null).

### Incursion (incursions/{incursion_id})

Campos de setup (PC):

- `index` (int).
- `spirit_1_id` (string).
- `spirit_2_id` (string).
- `board_1` (string).
- `board_2` (string).
- `board_layout` (string).
- `adversary_id` (string | null).
- `started_at` (timestamp | null).
- `ended_at` (timestamp | null).
- `exported` (bool).

Campos de juego (app):

- `adversary_level` (string | null).
- `difficulty` (int | null).
- `is_active` (bool).
- `result` ("win" | "loss").
- `player_count` (int).
- `invader_cards_remaining` (int).
- `invader_cards_out_of_deck` (int).
- `dahan_alive` (int).
- `blight_on_island` (int).
- `score` (int).

Desconocido / por confirmar:

- Uso real de `exported` (no se lee/escribe en app).

### Session (sessions/{session_id})

Campos observados:

- `started_at` (timestamp).
- `ended_at` (timestamp | null).

## Reglas de dominio (invariantes)

- Una sola incursion activa por Era (`active_incursion_id`).
- Un Periodo solo se puede revelar si el anterior tiene `ended_at` (si no es el primero).
- No se pueden asignar adversaries antes de `revealed_at`.
- Cada Periodo debe tener exactamente 4 incursions para asignar adversaries.
- En un Periodo, los 4 `adversary_id` deben ser distintos y no nulos.
- No se puede iniciar sesion si:
  - el Periodo no esta revelado,
  - el Periodo ya termino,
  - no hay `adversaries_assigned_at`,
  - ya hay otra incursion activa en la Era,
  - la incursion ya finalizo,
  - existe una session abierta.
- Primera session de una incursion requiere `adversary_level` y `difficulty` ya definidos.
- Solo una session abierta por incursion.
- Al finalizar incursion:
  - se cierra la session abierta,
  - se fija `ended_at`, `result`, metricas y `score`,
  - se limpia `active_incursion_id` y `active_incursion`,
  - si todas las incursions del Periodo tienen `ended_at`, se fija `period.ended_at`.
- El score es inmutable: no se puede finalizar dos veces.

## Flujos

### Generacion de Era (PC)

- `pc/generate_era.py` crea Era -> Periodos -> Incursions en Firestore.
- Puede generar un TSV de debug con el setup (`write_era_tsv`).

### Revelar Periodo (UI)

- Accion en `periods_screen` llama a `FirestoreService.reveal_period`.

### Asignar adversaries (UI)

- Dialogo en `periods_screen` llama a `FirestoreService.assign_period_adversaries`.

### Incursion: sesiones y finalizacion (UI)

- `incursion_detail_screen`:
  - seleccionar `adversary_level` actualiza `difficulty`.
  - `start_session` inicia una session (o una nueva si ya hubo sesiones).
  - `end_session` cierra la session abierta.
  - formulario de finalizacion calcula preview y llama `finalize_incursion`.

## Tiempo y formato

- Firestore almacena timestamps en UTC.
- La UI convierte a hora local via `format_datetime_local` y usa formato `dd/mm/yy HH:MM`.
- Si el valor no es parseable, se muestra un placeholder (guion largo en la UI).

## Score

Segun `app/services/score_service.py`:

- win: `5*difficulty + 10 + 2*invader_cards_remaining + player_count*dahan_alive - player_count*blight_on_island`
- loss: `2*difficulty + invader_cards_out_of_deck + player_count*dahan_alive - player_count*blight_on_island`

## Export TSV

- Existe export TSV de setup en `pc/generate_era.py` (debug).
- Export TSV de resultados finalizados: desconocido / por confirmar en el codigo actual.

## Inconsistencias detectadas

- README.md indica export TSV de resultados; en el codigo solo existe TSV de setup (debug) en `pc/generate_era.py`.
- README.md describe que `start_incursion` asigna `adversary_level`/`difficulty`; en el codigo la UI actualiza esos campos y `start_session` solo valida su existencia.
- DOCUMENTATION.md menciona `start_incursion`/`pause_incursion`/`resume_incursion`; en el codigo actual se usan `start_session`/`end_session` y no existe `resume_incursion` en app/services.
- DOCUMENTATION.md afirma que `get_active_incursion` recorre periodos/incursions; en el codigo actual solo lee `active_incursion_id` del documento de Era.
