# FLET_NOTES - Contrato UI (SpiritPlanner)

Documento de estilo para UI Flet en este repo.
No es canonico: la fuente de verdad es `TDD.md` y `adr/`.

## Principios
- UI declarativa y pragmatica.
- Separacion clara de responsabilidades.
- Evitar entropia por mutaciones dispersas.

## Separacion por archivos
- `*_screen.py`: composicion de UI.
- `*_state.py`: estado derivado (puro, sin Flet ni Firestore).
- `*_handlers.py`: efectos (Firestore, navegacion, dialogs, snackbars).

## Updates (orden preferente)
1) `control.update()`.
2) Rebuild de una seccion (reemplazar `content`/`controls` y actualizar el contenedor).
3) `page.update()` solo para overlays o navegacion.

## Overlays
- Crear dialogos en un unico lugar.
- Asignar a `page.dialog` / `page.bottom_sheet` y abrir/cerrar.
- Validar -> escribir -> cerrar -> refrescar solo lo necesario.

## Listas y tablas
- Listados: `ListView` o `Column(scroll=...)`.
- Tablas: `DataTable` cuando aporte legibilidad.
- El contenedor del listado es el punto de update.

## Routing (vigente) y migracion futura (requiere ADR)
- Routing actual: helpers `go` / `go_to` y enrutado centralizado en `app/main.py`.
- No cambiar routing ni migrar a otro esquema sin ADR especifico.
- Nota: cualquier intento de migrar el routing a otro patron (incl. `page.views` cookbook) requiere ADR.

## Idioma
- Nombres tecnicos en ingles.
- Textos de UI en castellano.

## Checklist rapido
- UI declarativa, sin Firestore directo en composicion.
- Updates disciplinados (no `page.update()` indiscriminado).
- Routing intacto, cambios con ADR.
- PRs en castellano.
