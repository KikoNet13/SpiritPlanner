# SpiritPlanner – Project Status

## Estado actual

- Backend Android (FirestoreService):
  - Implementado y validado contra el README.
  - Reglas duras enforced en backend.
  - Campo derivado `active_incursion` funcionando.
- Generador de Era (PC):
  - Funcional y estable.
  - Escribe directamente en Firestore.
- Script de pruebas manuales:
  - Ejecutado con éxito contra Firestore real.
  - Flujos válidos e inválidos comprobados.

- App Android (Flet):
  - Generada automáticamente por Codex.
  - Estructura básica de pantallas existente.
  - **Pendiente de revisión funcional y pruebas manuales**.

## Decisiones cerradas

- Firestore (Spark) es la única fuente de verdad.
- Backend Android es la barrera de validación (no la UI).
- Modelo de datos y reglas cerrados según README.
- Tests automáticos fuera de alcance por ahora.
- Tests manuales mediante scripts Python aceptados.

## Foco actual

- Revisión y ajuste de pantallas Flet:
  - comprobar que leen/escriben correctamente
  - detectar incoherencias con README
  - eliminar o corregir flujos inválidos
- Pruebas manuales de la app Android contra Firestore real.

## Fuera de alcance (por ahora)

- Exportación directa a BGG.
- Estadísticas avanzadas.
- Soporte multijugador.
- Optimización de rendimiento.
