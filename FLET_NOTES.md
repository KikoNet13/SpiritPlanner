# FLET_NOTES (SpiritPlanner) — Guía operativa de UI (NO CANÓNICA)

> ⚠️ NO CANÓNICO · ver `TDD.md` y `adr/` (especialmente ADR 0006).

---

## 1) Alcance y fuentes de verdad

Este documento resume cómo trabajar en Flet dentro del repo. Si contradice `TDD.md` o `adr/`, **manda TDD/ADR**.

---

## 2) Contrato de routing declarativo (ADR 0006)

**Contrato operativo (obligatorio):**

- Entry-point: `page.render_views(App)`.
- Stack: `App()` devuelve `list[ft.View]` reconstruida desde `page.route`.
- Navegación forward: **solo** `page.push_route(route)`.
- Back: `page.on_view_pop` empuja la ruta anterior con `page.push_route(previous_route)`.
- Prohibido mutar `page.views` manualmente.
- Router/coordinator **vive en memoria** (registro por `Page`), **no** en `page.session` ni `client_storage`.
- Si un handler síncrono necesita lanzar async, usar el mecanismo real de Flet en el repo (p.ej. `page.run_task(...)`).

**Notas operativas:**

- `go()`/`go_to()` son wrappers históricos y están **obsoletos** para código nuevo.
- Crear `ft.View` con keywords (`ft.View(route="/x", controls=[...])`) para evitar bugs en Flet.

---

## 3) UI declarativa / MVVM (operativo)

- Screen ViewModels: **sin** dependencia de `page` ni APIs de navegación.
- Views: responsables de efectos UI (snackbars, dialogs) con `ft.use_effect(...)` y `page = ft.context.page`.
- Coordinator/router (nivel app): permitido para routing global (`on_view_pop`, flujos compartidos).

---

## 4) Hooks / estado (estándar del proyecto)

- `use_state` **sin lambdas y sin `[0]`**:
  - `vm, _ = ft.use_state(MyViewModel())`
- El ViewModel se instancia **sin dependencias** (evitar pasar servicios por constructor del VM desde `use_state`).

---

## 5) Servicios (inyección recomendada)

- Los servicios se obtienen **desde la View** (no en el VM).
- Preferir registro en memoria por `Page` o providers de módulo.
- Evitar guardar objetos vivos en `page.session` / `client_storage` (especialmente router/coordinator).

---

## 6) Updates / refresh (disciplina)

Preferencia:

1) Reactividad (re-render por cambios en `@ft.observable`).
2) Actualizaciones puntuales: `control.update()` solo si es imprescindible.
3) `page.update()` solo para overlays o casos excepcionales.

Overlays:

- Diálogos/snackbars se disparan desde la View.
- Evitar crear `Controls` globales fuera de contexto de render (puede provocar errores de renderer).

---

## 7) NO HACER (anti-patrones)

- Mezclar `page.go()` con `page.push_route()`.
- `page.views.pop()` o mutaciones manuales de `page.views`.
- Guardar objetos vivos en `page.session` o `client_storage`.

---

## 8) Checklist de PR (routing/UI)

- ¿Usa `page.render_views(App)` y reconstruye views desde `page.route`?
- ¿La navegación forward usa **solo** `page.push_route()`?
- ¿El back evita mutar `page.views` y usa `page.on_view_pop` + `push_route(previous_route)`?
- ¿Screen ViewModels siguen sin depender de `page`?
- ¿Los efectos UI están en la View (`ft.use_effect`, snackbars, dialogs)?
- ¿No se guardan objetos vivos en `page.session` / `client_storage`?
- ¿Si hay async desde handlers sync, se usa `page.run_task(...)`?
- ¿Las `ft.View` se crean con keywords (`route=`, `controls=`)?

---

## 9) Debug: HUD y logs

- `SPIRITPLANNER_DEBUG=1` habilita HUD de depuración (ruta/top/vistas/pantalla).
- Logs a mantener en INFO:

  - CLICKs relevantes.
  - Navigate start/complete.
  - Route change handled (con `top_route`, `built_routes`).

- WARN solo para mismatches reales (route vs top vs built_routes).
- Bajar ruido de módulos verbosos (catálogos, `google*`, `urllib3`, etc.) a WARNING.

