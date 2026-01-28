# Flet Cookbook — Declarative vs Imperative CRUD (resumen operativo)

Fuente: “Declarative vs Imperative CRUD app” (Flet Cookbook). :contentReference[oaicite:1]{index=1}

## 1) Idea central: cambio de mentalidad

**Imperativo** (UI-first):

- Los handlers **mutan controles** directamente: `visible`, `value`, añadir/quitar controles, etc.
- Luego se fuerza el refresco con `page.update()`. :contentReference[oaicite:2]{index=2}

**Declarativo** (model-first):

- Los datos del modelo son la **fuente de verdad**.
- Los handlers **mutan estado/modelo**, no la vista.
- La UI se reconstruye como **función del estado**: **UI = f(state)**.
- Evitar `page.update()` como mecanismo habitual: el rerender viene por reactividad del estado. :contentReference[oaicite:3]{index=3}

> Nota: el ejemplo declarativo del cookbook usa `page.render(AppView)`. En nuestro repo podemos aplicar el enfoque declarativo *dentro de una pantalla* sin migrar el routing, pero el principio “UI = f(state)” se mantiene. :contentReference[oaicite:4]{index=4}

## 2) Building blocks declarativos en Flet

### 2.1 Observables = fuente de verdad (estado “duradero”)

`@ft.observable` convierte una dataclass en reactiva:

- Asignar a sus campos o modificar colecciones (append/remove) dispara re-render
- Sin `page.update()`. :contentReference[oaicite:5]{index=5}

Cuándo usar observables:

- Datos de dominio/persistentes (lo que “existe” en el modelo y se guarda).

### 2.2 Components = funciones que devuelven UI

`@ft.component` marca una función como unidad de render:

- Recibe props
- Puede usar hooks
- Devuelve controles que describen la UI para el estado actual
- No “parchea” el árbol de UI imperativamente; lo **describe**. :contentReference[oaicite:6]{index=6}

### 2.3 Hooks = estado local/transitorio de UI

`ft.use_state` y similares:

- Los componentes se re-ejecutan en cada render; variables locales “normales” se reinicializan.
- Los hooks guardan estado entre renders y **programan re-render** al cambiar.
- Útil para flags de UI (p.ej. `is_editing`) y buffers de inputs dentro del componente. :contentReference[oaicite:7]{index=7}

Regla práctica (cookbook):

- **Hooks**: estado local y efímero del componente (solo UI).
- **Observables**: estado duradero/compartido o persistente. :contentReference[oaicite:8]{index=8}

## 3) “UI = f(state)” en dos fases

1) **Evento → actualiza estado**

- El handler cambia datos (modelo observable o hook state).
- No oculta/muestra controles ni llama a `page.update()`. :contentReference[oaicite:9]{index=9}

1) **Render → UI derivada del estado**

- El componente retorna controles según el snapshot actual del estado.
- Flet re-renderiza el subárbol afectado al detectar cambios en observables/hooks. :contentReference[oaicite:10]{index=10}

## 4) Recetas de migración (imperativo → declarativo)

### 4.1 Toggles de `visible` → Render condicional

Imperativo:

- `control.visible = False/True`
- `page.update()`

Declarativo:

- `return A if condition else B` (dos árboles UI alternativos). :contentReference[oaicite:11]{index=11}

### 4.2 Mutación directa de controles → Mutación del modelo

Imperativo:

- `text.value = "..."`
Declarativo:
- `user.update(...)` o asignación sobre estado observable. :contentReference[oaicite:12]{index=12}

### 4.3 `page.update()` en todas partes → “Nowhere”

- Imperativo: handlers acaban con `page.update()`.
- Declarativo: cambias estado y dejas que Flet re-renderice. :contentReference[oaicite:13]{index=13}

### 4.4 Handlers manipulan estado, no la vista

Ejemplos declarativos:

- `set_is_editing(True)`
- `set_new_first_name(user.first_name)` :contentReference[oaicite:14]{index=14}

### 4.5 Extraer UI en componentes

Dividir la pantalla en piezas:

- un componente por fila/row
- un componente por formulario/dialog
- un componente por sección de lista, etc. :contentReference[oaicite:15]{index=15}

## 5) Anti-patrones (señales de que sigues en imperativo)

- Handlers que:
  - tocan `visible/value/controls.append/remove` directamente sobre controles de UI
  - llaman a `page.update()` para “refrescar la pantalla”
- Estado duplicado:
  - mantener “la verdad” en controles (TextField.value) y en modelo a la vez
- Variables locales usadas como estado (se pierden en re-render, no refrescan). :contentReference[oaicite:16]{index=16}

## 6) Beneficio esperado

Según el cookbook:

- En apps pequeñas puede parecer similar,
- pero conforme crece la pantalla, el enfoque declarativo te hace añadir **estado y componentes**, no mutaciones dispersas de controles.
- Resultado: código más mantenible y fácil de cambiar, sin perseguir flags `visible` ni updates manuales. :contentReference[oaicite:17]{index=17}
