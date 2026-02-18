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

## Routing / navegacion (Flet declarativo)

Fuente normativa: `adr/0006-flet-declarative-routing-contract.md`.

Contrato canonico:

- Render declarativo: el entrypoint usa `page.render_views(App)`.
- Fuente de verdad: `page.route`.
- El stack de pantallas se reconstruye en cada render como `list[ft.View]` a partir de `page.route` (p.ej. `build_route_stack(route)`).
- Navegacion forward: usar **solo** `page.push_route(route)`.
- Prohibido usar `page.go()` para navegacion normal y prohibido mezclar `go()` con `push_route()`.
- Back: `page.on_view_pop` **no** muta `page.views` manualmente (no `page.views.pop()`); navega empujando la ruta anterior (p.ej. `page.push_route(previous_route)`).
- Creacion de views: usar siempre keywords (`ft.View(route="...", controls=[...])`), evitando args posicionales.
- Helpers `go`/`go_to` (si existen) deben envolver `page.push_route()` o se consideran obsoletos.

Resolucion de rutas:

- Match por especificidad (mas especifica primero, generica al final):
  1) `.../incursions/{incursion_id}`
  2) `.../periods/{period_id}`
  3) `/eras/{era_id}`
  4) `/eras`

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
- `dahan_alive` (int).
- `blight_on_island` (int).
- `player_count` (int).
- `invader_cards_remaining` (int).
- `invader_cards_out_of_deck` (int).
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
- En `incursion_detail_view`, el cronometro total y la duracion de cada sesion se muestran como `HH:MM:SS`.
- Si el valor no es parseable, se muestra un placeholder (guion largo en la UI).

## Visibilidad de score en UI

- Lista de incursiones (`incursions_view`): cada tarjeta muestra `Puntuacion` con valor numerico o `—` si no hay score.
- Lista de periodos (`periods_view`): cada tarjeta muestra:
  - `Puntuacion total` parcial (suma de incursiones con `score`),
  - `Media/incursion` calculada sobre incursiones finalizadas (`score` presente), con 2 decimales o `—` si no hay finalizadas.
- Lista de eras (`eras_view`): cada tarjeta muestra los mismos agregados (`Puntuacion total` y `Media/incursion`) acumulados sobre todos sus periodos.

## Score

Segun `adr/0007-rulebook-scoring.md`:

- Win:
  - `score = 5*difficulty + 10 + 2*invader_cards_remaining + player_count*dahan_alive - player_count*blight_on_island`
- Loss:
  - `score = 2*difficulty + 1*invader_cards_out_of_deck + player_count*dahan_alive - player_count*blight_on_island`

Nota:

- La app es solo 2 jugadores: `player_count` no se edita en UI y se fija a 2 al finalizar.

## Export TSV

- Existe export TSV de setup en `pc/generate_era.py` (debug).
- Export TSV de resultados finalizados: desconocido / por confirmar en el codigo actual.

## Inconsistencias detectadas

- README.md indica export TSV de resultados; en el codigo solo existe TSV de setup (debug) en `pc/generate_era.py`.
- README.md describe que `start_incursion` asigna `adversary_level`/`difficulty`; en el codigo la UI actualiza esos campos y `start_session` solo valida su existencia.
- DOCUMENTATION.md menciona `start_incursion`/`pause_incursion`/`resume_incursion`; en el codigo actual se usan `start_session`/`end_session` y no existe `resume_incursion` en app/services.
- DOCUMENTATION.md afirma que `get_active_incursion` recorre periodos/incursions; en el codigo actual solo lee `active_incursion_id` del documento de Era.
