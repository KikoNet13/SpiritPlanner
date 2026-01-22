# SpiritPlanner – Project Status

## Estado actual

- Generador de Era en Python funcional.
- Estructura validada:
  - Round-robin de espíritus (2 espíritus por incursión).
  - Boards equilibrados por periodo:
    - cada board aparece exactamente 2 veces
    - máxima variedad de parejas por periodo.
  - Layouts equilibrados y variados.
  - Randomización superficial determinista mediante seed explícito.
- El generador actualmente exporta TSV SOLO como output de test/debug.
- El generador NO se considera finalizado.

## Decisiones cerradas

- Firestore será la única fuente de verdad.
- Android (Flet):
  - consume y actualiza estado
  - NO genera estructura de Era.
- PC (Python):
  - genera estructura inicial
  - realiza tareas de administración.
- TSV no es formato final ni persistente.

## Pendiente / Próximo paso

- Definir el modelo de datos en Firestore para:
  - Era
  - Periodo
  - Incursión
- Migrar la generación de Era a Firestore.
- Eliminar la dependencia de TSV como output principal.

## Fuera de alcance (por ahora)

- Exportación final a BGG.
- Estadísticas avanzadas.
- Soporte multijugador.
