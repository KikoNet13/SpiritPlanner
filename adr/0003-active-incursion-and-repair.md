# ADR 0003 - Active incursion pointer y repair seguro

Status: Accepted

## Contexto
El sistema necesita identificar una unica incursion activa por Era.
En el codigo existe un puntero derivado en `eras/{era_id}` (`active_incursion_id` y `active_incursion`).
Si ese puntero se desincroniza, la UI puede quedar inconsistente.

## Decision
- La fuente de verdad sigue siendo la incursion (sus campos y sesiones), pero se mantiene un puntero derivado en la Era para acceso rapido.
- `active_incursion_id` usa el formato `{period_id}::{incursion_id}`.
- El puntero se escribe al iniciar sesion (`start_session`) y se limpia al finalizar (`finalize_incursion`).
- No se implementa reparacion automatica en la app; cualquier repair es manual/administrativo.

## Repair seguro (manual)
1) Identificar incursions con `is_active == True` y/o sessions abiertas.
2) Validar que solo exista una activa en la Era.
3) Actualizar `active_incursion_id` y `active_incursion` o limpiarlos si no hay activa.

Desconocido / por confirmar:
- Script o procedimiento automatizado para repair en `pc/`.

## Consecuencias
- La UI depende del puntero derivado para navegar a la incursion activa.
- Cualquier inconsistencia requiere accion manual.

## Referencias
- `app/services/firestore_service.py`
- `app/screens/eras/eras_handlers.py`
