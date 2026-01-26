# SpiritPlanner – Project Status

## Estado general

El proyecto está en fase de **estabilización**, con la estructura base y varias pantallas ya creadas, pero con **bloqueos funcionales** en la pantalla más crítica: **detalle de Incursión**.

El foco actual es:

- corregir lógica de sesiones y nivel/dificultad en detalle de Incursión,
- consolidar flujos y estados según README,
- evitar sobreestilado y mantener UI simple y mantenible.

---

## Estado funcional (real)

### Funciona / parcialmente funcional

- Estructura y navegación general de la app (Eras → Periodos → Incursiones → Detalle) existente.
- Firestore se usa como **fuente de verdad**.
- Se muestran datos principales de la Incursión (espíritus, tableros, adversario, layout).
- El cálculo de duración total puede mostrar valores extremos si en Firestore hay sesiones manipuladas (caso de prueba válido).

### NO funciona / bloquea el uso (prioridad alta)

**Pantalla de detalle de Incursión:**

- No se puede iniciar sesiones desde la UI (control PLAY/STOP no operativo).
- No aparece un control usable en Windows para simular el FAB (y el FAB tampoco está resolviendo el flujo en debug).
- Selector de nivel del adversario:
  - legibilidad insuficiente en fondo oscuro,
  - selección no persistente en Firestore,
  - dificultad no recalculada/mostrada de forma fiable.
- En consecuencia, el flujo “seleccionar nivel → iniciar sesión” queda bloqueado.

### Finalización de incursión

- Existe UI/modal de finalización y captura de datos, pero su funcionamiento real debe considerarse **pendiente de validación** hasta que el flujo de sesiones y nivel/dificultad esté estabilizado.

---

## UI / UX

- Objetivo final: tablet Android en horizontal.
- Desarrollo y debug: Windows.
- La UI está en fase de ajuste:
  - priorizar alineación, jerarquía visual y componentes Flet estándar,
  - evitar “colores uno a uno” que degradan mantenibilidad,
  - preparar base para componentes reutilizables más adelante (sin re-arquitectura aún).

---

## Arquitectura y código

- Código mayoritariamente funcional/procedimental.
- Riesgo actual: funciones demasiado largas y demasiada lógica anidada en pantallas (especialmente Incursión), lo que dificulta depuración y cambios manuales.
- Enfoque inmediato: correcciones puntuales y refactor mínimo orientado a legibilidad (sin rediseño global).

---

## Documentación

- README.md sigue siendo la **fuente canónica** de reglas, modelo y alcance.
- DOCUMENTATION.md se está usando como soporte para entender el código, pero no sustituye validación funcional.

---

## Pendiente / siguiente foco

1) Arreglar detalle de Incursión:

- control PLAY/STOP operativo (Android + alternativa clara en Windows),
- selector de nivel persistente y legible,
- dificultad recalculada correctamente,
- validar estados con datos limpios.

1) Tras estabilizar lo anterior:

- revisar organización interna del fichero de pantalla para reducir complejidad (sin introducir sobreingeniería).

---
