# SpiritPlanner – Project Status

## Estado general

Fase de **estabilización**. Se ha reorganizado la mitad inferior de la pantalla de **detalle de Incursión**: contador total en vivo, acciones alineadas y sesiones visibles en una tabla ligera (DataTable). Aún falta validar el flujo completo de sesiones y el selector de nivel/dificultad.

Foco inmediato:

- Validar inicio/fin de sesión y persistencia de nivel/dificultad.
- Mantener la UI funcional y alineada al README, evitando sobreestilado.

---

## Estado funcional (real)

### Funciona / parcialmente funcional

- Navegación general (Eras → Periodos → Incursiones → Detalle).
- Firestore como fuente de verdad.
- Datos principales de la incursión visibles (espíritus, tableros, adversario, layout).
- Tiempo total mostrado y actualizado en vivo cuando hay sesión abierta.
- Sesiones visibles en DataTable con fecha, rango horario y duración; sesión abierta muestra rango “–ahora” y duración “—”.
- El cálculo de duración total puede mostrar valores extremos si en Firestore hay sesiones manipuladas (caso de prueba válido).

### No funciona / bloquea (prioridad alta)

- Flujo de inicio/fin de sesión pendiente de validación end-to-end (UI rediseñada, lógica no tocada en esta iteración).
- Selector de nivel del adversario: persistencia y recálculo de dificultad pendientes de comprobación; legibilidad en fondo oscuro mejorable.

---

## UI / UX

- Objetivo: tablet Android horizontal; desarrollo y debug en Windows.
- UI ajustada para jerarquía clara y componentes Flet estándar; sesiones ahora en tabla compacta.

---

## Arquitectura y código

- Código mayormente funcional/procedimental con funciones largas en pantallas; riesgo de complejidad en detalle de incursión.
- Enfoque: correcciones puntuales y refactor mínimo orientado a legibilidad sin re-arquitectura global.

---

## Documentación

- README.md sigue siendo la fuente canónica de reglas y alcance.
- DOCUMENTATION.md sirve de apoyo, no sustituye validación funcional.

---

## Pendiente / siguiente foco

1) Detalle de incursión: validar PLAY/STOP, persistencia de nivel y recálculo de dificultad; ajustar visual del selector si es necesario.
2) Tras estabilizar: simplificar el fichero de pantalla para reducir complejidad sin sobreingeniería.
