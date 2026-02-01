# AGENTS

Reglas de trabajo para agentes y PRs en este repo.

## Fuentes de verdad (orden)

1) `TDD.md`
2) `adr/`
3) Codigo del repo (implementacion)

No canonico: `README.md`, `STATUS.md`, `DOCUMENTATION.md`, `FLET_NOTES.md`.

## Idioma

- Nombres tecnicos (clases, funciones, campos, rutas, archivos): ingles.
- UI, docs y PRs: castellano.

## Estilo Flet y actualizaciones

- UI declarativa y composicion clara.
- `*_state.py`: estado derivado/puro.
- `*_handlers.py`: efectos (Firestore, navegacion, dialogs, snackbars).
- Actualizaciones preferentes: `control.update()` > rebuild de seccion > `page.update()` (solo overlays/navegacion).
- Evitar refactors grandes a medias.

## Routing (critico)

- Contrato unico (ADR 0006 + TDD):

  - Entry-point: `page.render_views(App)`.
  - Stack: `App()` devuelve `list[ft.View]` reconstruida desde `page.route`.
  - Navegacion forward: **solo** `page.push_route(route)`.
  - Prohibido: `page.go()` para navegacion normal.
  - Back: `page.on_view_pop` **no** muta `page.views` manualmente (no `page.views.pop()`); navega empujando la ruta anterior con `page.push_route(previous_route)`.

- Helpers (`go()` / `go_to()`):

  - Envoltorios de `push_route` o **obsoletos; no usar en codigo nuevo**.
  - No pedir refactors aqui; solo documentacion.

- MVVM:

  - Screen ViewModels: no dependen de `page` ni de APIs de navegacion.
  - App-level coordinator/router: puede manejar `on_view_pop` y disparar navegacion (routing global permitido).

- Nota: Si un PR introduce `page.go()` o `page.views.pop()` manual para navegacion, se considera desviacion del contrato y debe corregirse.

- Prohibido cambiar routing sin ADR especifico.

## Markdown (higiene y lint)

Reglas para evitar errores típicos de markdownlint (especialmente MD041, MD022, MD032):

- **MD041 (first-line-h1):** la **primera línea** del fichero debe ser un H1 `# ...`.
- **MD022 (blanks-around-headings):** dejar **1 línea en blanco** después de cada encabezado.
- **MD032 (blanks-around-lists):** dejar **1 línea en blanco** antes y después de cada lista.

Banner “NO CANÓNICO”:

- Mantener el **título real** como H1.
- Poner el banner **debajo** como quote (recomendado), por ejemplo:
  - `> ⚠️ NO CANÓNICO · ver TDD.md y adr/`
- No poner texto antes del H1.

Checklist rápido antes de commitear docs:

- ¿El fichero empieza por `# ...`?
- ¿Hay línea en blanco tras cada heading?
- ¿Hay línea en blanco antes/después de listas?

## Reglas de PR

- PRs en castellano.
- Si hay discrepancias con TDD/ADR, documentarlas.
- No tocar codigo sin solicitud explicita.
