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
- Routing centralizado en `app/main.py` y helpers `go` / `go_to`.
- Prohibido cambiar routing sin ADR especifico.

## Reglas de PR
- PRs en castellano.
- Si hay discrepancias con TDD/ADR, documentarlas.
- No tocar codigo sin solicitud explicita.
