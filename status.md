# SpiritPlanner – Project Status

## Estado actual

- Backend Android (FirestoreService):
  - Implementado contra versión anterior del README.
  - Requiere ajustes por:
    - eliminación de `started_at` en Period
    - incorporación de `adversaries_assigned_at`

- Generador de Era (PC):
  - Funcional.
  - Debe revisarse para asegurar compatibilidad con el modelo actualizado.

- App Android (Flet):
  - Estructura básica existente.
  - Pendiente de:
    - flujo correcto de Periodos
    - pantalla/modal de asignación de adversarios
    - botones únicos por estado

- Scripts de pruebas manuales:
  - Revisión necesaria si referencian campos antiguos.

---

## Decisiones cerradas

- Firestore es almacenamiento, sin Security Rules.
- El flujo se controla desde UI + código.
- `revealed_at` es el inicio real del Periodo.
- No existe `started_at` en Period.
- La asignación de adversarios es un paso explícito.
- El botón visible define el estado.

---

## Foco actual

1. Alinear código con README actualizado.
2. Implementar asignación de adversarios.
3. Ajustar lista de Periodos al flujo.
4. Pruebas manuales end-to-end.

---

## Fuera de alcance

- Exportación directa a BGG
- Estadísticas avanzadas
- Multijugador
- Optimización
