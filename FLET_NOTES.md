# FLET_NOTES (SpiritPlanner) — Guía operativa de UI (NO CANÓNICA)

> **NO CANÓNICO.**
> La fuente de verdad es:
>
> 1) `TDD.md`
> 2) `adr/*` (especialmente **ADR 0005**, contrato vigente de UI/MVVM)
>
> Si este fichero contradice TDD/ADR, **gana TDD/ADR**. Este documento solo resume “cómo trabajamos” en Flet.

---

## 1) Arquitectura UI vigente (MVVM declarativa)

**Tripletas por pantalla:**

- `*_model.py`: `@dataclass` (datos + helpers puros opcionales)
- `*_viewmodel.py`: `@ft.observable` (estado + intents; **sin `page`**)
- `*_view.py`: `@ft.component` + hooks (render + efectos UI)

**Reglas clave:**

- ViewModel “puro”: no guarda `page`, no crea `Controls`, no muestra diálogos/snackbars.
- Efectos UI (navegación, snackbars, diálogos) **solo desde la View**, usando:
  - `page = ft.context.page`
  - `ft.use_effect(...)` para reaccionar a cambios de estado/intents

---

## 2) Hooks / estado (estándar del proyecto)

- `use_state` **sin lambdas y sin `[0]`**:
  - `vm, _ = ft.use_state(MyViewModel())`
- El ViewModel se instancia **sin dependencias** (evitar pasar servicios por constructor del VM desde `use_state`).

---

## 3) Servicios (inyección recomendada)

- Los servicios se obtienen **desde la View** (no en el VM), idealmente desde un singleton en `page.session`.
- La View pasa `service` a métodos del VM cuando haga falta.
- Objetivo: evitar VMs acoplados al runtime/UI.

---

## 4) Routing / navegación (declarativo)

**Contrato operativo:**

- Stack se recompone desde `page.route` con `page.render_views(build_views)`.
- Navegación **unificada**: usar **solo `page.go(route)`** (no mezclar con `push_route()`).
- Back: `on_view_pop` hace `page.views.pop()` y luego `page.go(page.views[-1].route)`.

**Muy importante (Flet issue #5943):**

- Crear las views **SIEMPRE** con keywords:
  - `ft.View(route="/eras/1", controls=[...])`
- Evitar `ft.View("/eras/1", [...])` (posicional), por comportamiento errático en algunas versiones.

**Resolución de rutas:**

- Match de rutas **por especificidad** (más específica primero, genérica al final):
  1) `.../incursions/{incursion_id}` (detalle)
  2) `.../periods/{period_id}` (incursions list)
  3) `/eras/{era_id}` (periods list)
  4) `/eras` (eras list)

---

## 5) Updates / refresh (disciplina)

Preferencia:

1) Reactividad (re-render por cambios en `@ft.observable`).
2) Actualizaciones puntuales: `control.update()` solo si es imprescindible.
3) `page.update()` solo para overlays o casos excepcionales.

Overlays:

- Diálogos/snackbars se disparan desde la View.
- Evitar crear `Controls` globales fuera de contexto de render (puede provocar errores de renderer).

---

## 6) Debug: HUD y logs

- `SPIRITPLANNER_DEBUG=1` habilita HUD de depuración (ruta/top/vistas/pantalla).
- Logs a mantener en INFO:
  - CLICKs relevantes
  - Navigate start/complete
  - Route change handled (con `top_route`, `built_routes`)
- WARN solo para mismatches reales (route vs top vs built_routes).
- Bajar ruido de módulos verbosos (catálogos, `google*`, `urllib3`, etc.) a WARNING.

---

## 7) Checklist rápido antes de pedir cambios a Codex

- ¿La tarea respeta `TDD.md` y `adr/*`?
- ¿VM sin `page` y efectos solo en View?
- ¿`ft.View(route=..., controls=...)` en todas las rutas?
- ¿Navegación solo con `page.go()`?
- ¿`use_state` con `vm, _ = ...`?
- ¿Servicios leídos desde la View (p.ej. `page.session`)?
