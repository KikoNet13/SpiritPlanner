# SpiritPlanner – Project Status

## Estado actual

- Generador de Era en Python funcional y conectado a Firestore.
- Estructura validada:
  - Round-robin de espíritus (2 espíritus por incursión).
  - Boards equilibrados por periodo:
    - cada board aparece exactamente 2 veces
    - máxima variedad de parejas por periodo.
  - Layouts equilibrados y variados.
  - Randomización superficial determinista mediante seed explícito.
- El generador:
  - escribe directamente en Firestore (Era, Periodos, Incursiones)
  - usa IDs deterministas
  - aborta si la Era ya existe
- Exportación TSV:
  - mantenida solo como output de test/debug
  - no es formato persistente ni fuente de verdad.

## Decisiones cerradas

- Firestore (Spark) es la única fuente de verdad.
- Modelo de datos en Firestore:
  - definido
  - validado
  - alineado con el README.
- Separación de responsabilidades:
  - Android (Flet):
    - consume y actualiza estado
    - NO genera estructura de Era.
  - PC (Python):
    - genera estructura inicial de la Era
    - realiza tareas de administración.
- TSV no es formato final ni persistente.

## Próximo foco

- Desarrollo de la app Android (Flet):
  - lecturas desde Firestore
  - escrituras controladas según reglas del README
  - gestión de estado (revelar Periodos, iniciar/finalizar Incursiones, sesiones).

## Fuera de alcance (por ahora)

- Exportación directa a BGG.
- Estadísticas avanzadas.
- Soporte multijugador.
