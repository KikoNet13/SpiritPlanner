# SpiritPlanner - Status (NO CANONICO)

> NO CANONICO. Puede estar desactualizado. Ver `TDD.md` y `adr/`.

## Estado real (segun codigo)
- UI Flet con pantallas: Eras, Periodos, Incursions, Incursion detail.
- Routing centralizado en `app/main.py` con helpers `go`/`go_to`.
- FirestoreService implementa: `reveal_period`, `assign_period_adversaries`, `start_session`, `end_session`, `finalize_incursion`, `update_incursion_adversary_level`.
- Scripts PC: `pc/generate_era.py` y `pc/firestore_service.py`.
- Tests manuales: `tests/manual_firestore_checks.py` (manual, sin automatizacion).

## Foco actual
- Consolidar contrato declarativo de UI (ADR 0002 / FLET_NOTES).
- Validacion end-to-end del flujo de sesiones y finalizacion (estado desconocido).
- Aclarar export TSV de resultados (no visible en codigo actual).

## Riesgos
- Entropia de UI por actualizaciones dispersas.
- Cambios de routing sin ADR.
- Puntero `active_incursion_id` desincronizado sin repair.
