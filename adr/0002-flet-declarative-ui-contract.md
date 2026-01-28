# ADR 0002 - Flet declarative UI contract

Status: Accepted

## Contexto

La UI en Flet puede derivar en entropia si se mezclan efectos, mutaciones y `page.update()` indiscriminado.
Se necesita un contrato estable para mantener el codigo legible y predecible.

## Decision

- UI declarativa y composicion clara en `*_screen.py`.
- Estado derivado en `*_state.py` (funciones puras).
- Efectos en `*_handlers.py` (Firestore, navegacion, dialogs/snackbars).
- Actualizaciones preferentes: `control.update()` > rebuild de seccion > `page.update()` solo para overlays/navegacion.
- Routing centralizado en `app/main.py` y helpers `go`/`go_to`.
- Prohibido cambiar routing sin ADR especifico.

## Consecuencias

- Menos mutaciones dispersas y mas previsibilidad en UI.
- Cambios de routing o de patron de actualizacion requieren ADR.
- Se reduce el riesgo de refactors a medias.

## Referencias

- `FLET_NOTES.md`
- `app/main.py`
- `app/utils/navigation.py`
