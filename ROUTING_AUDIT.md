# Auditoría de routing vs ADR 0006

## Resumen ejecutivo

Se detectaron usos directos de `page.go(...)` y una mutación manual de `page.views.pop()`, ambos incompatibles con ADR 0006.
No se encontraron llamadas a `page.push_route(...)` en `app/`.
El entry-point `page.render_views(...)` y el hook `page.on_view_pop` sí están presentes.
Los helpers `go/go_to` existen y delegan en navegación basada en `page.go`, por lo que también bloquean el contrato.
Bloqueos principales para cumplir ADR 0006: reemplazar `page.go` y eliminar `page.views.pop()` en el flujo de back.

## Violaciones ADR 0006

- [VIOLATION] `app/main.py:250` — `page.views.pop()` en manejo de back.
- [VIOLATION] `app/main.py:251` — `page.go(...)` para navegar al back.
- [VIOLATION] `app/utils/navigation.py:16` — `page.go(...)` en helper `navigate`.
- [VIOLATION] `app/utils/navigation.py:19` — helper `go(...)` delega en `navigate` (usa `page.go`).
- [VIOLATION] `app/utils/navigation.py:23` — helper `go_to(...)` delega en `navigate` (usa `page.go`).

## OK / Alineado

- `app/main.py:185` — `page.render_views(build_views)`.
- `app/main.py:254` — `page.on_view_pop = handle_view_pop` (sin pop manual en esta línea).
- Sin ocurrencias de `page.push_route(...)` en `app/`.

## Top 5 cambios mínimos (solo propuesta, NO implementar)

- `app/utils/navigation.py`: hacer que `navigate/go/go_to` envuelvan `page.push_route(route)` en lugar de `page.go`.
- `app/main.py`: en el handler de back, reemplazar `page.views.pop()` por navegación con `page.push_route(previous_route)`.
- `app/main.py`: sustituir `page.go(page.views[-1].route)` por `page.push_route(...)` del route previo.
- `app/main.py`: centralizar el cálculo de `previous_route` para evitar acceso directo a `page.views` en lógica de navegación.
- `app/main.py`/`app/utils/navigation.py`: documentar en comentarios que `page.go` es incompatible con ADR 0006 y debe evitarse.
