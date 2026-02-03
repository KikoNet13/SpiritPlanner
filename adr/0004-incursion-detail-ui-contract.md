# ADR 0004 - Incursion detail UI contract

Status: Accepted

## Contexto

- Esta pantalla ya tiene un estilo y UX que no debe degradarse.
- Hay riesgo de entropia por refactors "declarativos" mal aplicados.
- Se alinea con ADR 0005 (contrato MVVM declarativo) y con el UI contract existente en `REPO_MAP.md`.

## Decision - UI contract

- Mantener `ft.AppBar` con titulo "Incursión" y `center_title=True`.
- Mantener el contenedor principal `ft.Container` con `padding=16`, `scroll=ft.ScrollMode.AUTO`, `expand=True` y `ft.Column([setup_section, bottom_section], spacing=16)`.
- Mantener `setup_section` como `dark_section` y `bottom_section` como `light_section`.
- Mantener el orden interno de `setup_section`: etiqueta "Incursión {index} · {period_label}" -> fila de spirits/boards -> `layout_name` -> placeholder de layout -> `ft.Divider` -> `adversary_level_block`.
- Mantener `adversary_level_block` como bloque centrado con nombre de adversary y selector o texto de nivel/dificultad.
- Mantener el orden interno de `bottom_section`: `time_text` -> boton principal -> `result_summary` (si finalizada) -> `finalize_panel` -> `sessions_detail`.
- NO cambiar el orden de secciones.
- NO cambiar los tamaños/anchos clave:
  - Boton principal `width=320` y `height=52`.
  - Placeholder de layout `height=140` y `width=240`.

Nota: el tamaño fijo del placeholder de layout queda superseded por ADR 0008.

## Decision - Interacciones

- Flujo formal: `start_session` -> `end_session` -> `finalize_incursion`.
- Precondiciones:
  - `start_session` requiere `adversary_level` y `difficulty` validos.
  - `finalize_incursion` cierra una session abierta antes de finalizar.
  - Estado `FINALIZED` bloquea acciones.
- El boton principal representa el estado de sesion (iniciar/terminar/reanudar) segun `resolve_session_state`.

## Decision - Puntos de update

- Jerarquia de updates: `control.update()` > rebuild de seccion > `page.update()` solo para overlays/navegacion.
- Puntos de update permitidos:
  - `adversary_level_block` (cambio de nivel/dificultad).
  - `time_text` (timer).
  - `sessions_detail` (al iniciar/terminar sesion).
  - `finalize_panel` / preview de score (al editar inputs).
  - `confirm_row` / dialog overlay (si existe).
- Prohibido `page.update()` global salvo overlays/navegacion.

## Consecuencias

- Cambios visuales en esta pantalla requieren justificacion en PR y/o ADR.
- Se evita refactorizar reordenando el layout.

## Referencias

- `REPO_MAP.md` (seccion incursion_detail_screen UI contract).
- ADR 0005.
- `FLET_NOTES.md`.
