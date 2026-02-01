# ADR 0006 - Flet declarative routing contract

Status: Accepted

## Contexto

Necesitamos un contrato de navegación estable en Flet usando el paradigma declarativo oficial, con una pila de pantallas navegable sin errores (forward/back) y con reconstrucción determinista de `views` a partir de la `route`.

Actualmente hay reglas/documentos internos que contradicen este enfoque (p.ej. “solo page.go” y “pop manual de page.views”), lo que genera ambigüedad y bugs.

Este contrato ya está implementado y validado en `main`.

## Decision

Adoptamos como contrato único de routing el siguiente patrón declarativo:

1) **Render declarativo**

- El entrypoint usa `page.render_views(App)`.

1) **Fuente de verdad**

- `page.route` es la fuente de verdad.
- La pila de pantallas (`list[ft.View]`) se reconstruye en cada render a partir de `page.route` mediante un builder (p.ej. `build_route_stack(route)`).

1) **Navegación**

- La navegación “forward” se hace **solo** con `page.push_route(route)`.
- No se usa `page.go()` para navegación normal dentro de la app (para evitar mezcla de contratos).

1) **Back (pop)**

- `page.on_view_pop` no muta `page.views` manualmente.
- Al ocurrir un pop, se navega a la ruta anterior empujando esa ruta (p.ej. `page.push_route(previous_route)`), manteniendo el flujo consistente con el stack reconstruido desde `route`.

1) **Responsabilidad de navegación y MVVM**

- Se permite que un **App-level model/coordinator** (router state) gestione eventos globales como `on_view_pop` y dispare navegación.
- Los **screen ViewModels** no deben acoplarse a `page` ni conocer APIs de navegación; solo exponen estado/acciones. La View decide cuándo llamar a `push_route` o delegar en el coordinator.

## Consecuencias

- ✅ Eliminamos la ambigüedad: un solo contrato (render_views + stack desde route + push_route).
- ✅ Back/forward predecible sin “pop manual” de `page.views`.
- ✅ Facilita depuración: la UI es una función de `route` + estado observable.

- ❗ Requiere actualizar documentación existente que menciona:
  - “solo page.go()”
  - `page.views.pop()` + `page.go(page.views[-1].route)`
  - helpers/handlers imperativos basados en mutación directa de views

## Referencias

- Ejemplo oficial de Flet (routing declarativo): `sdk/python/examples/apps/declarative/routing_two_pages.py`
- Ejemplo objetivo del repo (Atlas Boreal): `main.py` y su documentación asociada
