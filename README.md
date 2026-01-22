# SpiritPlanner

Herramienta para gestionar campañas en solitario de **Spirit Island** usando **Firestore** como fuente de verdad.

Permite generar campañas completas, jugar incursiones con control de tiempo por sesiones, calcular puntuaciones y exportar resultados a **TSV** para análisis externo (Google Sheets / BGG).

---

## Objetivo

- Gestionar **Eras**, **Periodos** e **Incursiones**
- Jugar Incursiones en orden libre dentro de cada Periodo
- Registrar tiempo real mediante sesiones (pausa/reanudación)
- Calcular puntuaciones de forma consistente
- Exportar resultados a TSV

Fuera de alcance cualquier funcionalidad no relacionada con lo anterior.

---

## Stack tecnológico

- **Firestore (Spark)** → fuente única de verdad
- **Android (Flet)** → UI principal (lectura/escritura)
- **PC (scripts / CLI Python)** → generación de Era y exportación TSV
- **Google Sheets** → diario y preparación manual para BGG

---

## Regla global de idioma (CRÍTICA)

- **Código, modelos, campos, colecciones, scripts → INGLÉS**
- **Interfaz de usuario → CASTELLANO**

Nunca mezclar idiomas en nombres técnicos.

---

## Modelo de datos (Firestore)

### Estructura general

```text
eras/{era_id}
  periods/{period_id}
    incursions/{incursion_id}
      sessions/{session_id}
```

---

### Era (`eras/{era_id}`)

- `is_active` (bool)
- `created_at` (timestamp UTC)

---

### Period (`periods/{period_id}`)

- `index` (int)
- `created_at` (timestamp UTC)
- `revealed_at` (timestamp | null)
- `started_at` (timestamp | null)
- `ended_at` (timestamp | null)

Reglas:

- Los Periodos se revelan **secuencialmente**
- Solo se puede revelar un Periodo si el anterior está finalizado

---

### Incursion (`incursions/{incursion_id}`)

#### Identidad

- `index` (int)

#### Setup base (solo PC, inmutable)

- `spirit_1_id` (string)
- `spirit_2_id` (string)
- `board_1` (string)
- `board_2` (string)
- `board_layout` (string)

#### Asignación estratégica (al revelar Periodo)

- `adversary_id` (string | null)

> Al revelar un Periodo, el adversario se asigna **a cada Incursión del Periodo**.

#### Al iniciar la Incursion

- `adversary_level` (string | null)
- `difficulty` (int)

> Escenarios se tratan como adversarios.  
> El nivel es texto libre (ej. “Base”, “Nivel 3”, “Rituales de terror”).

#### Estado temporal

- `started_at` (timestamp | null)
- `ended_at` (timestamp | null)

#### Score

- `result` (`"win"` / `"loss"`)
- `player_count` (int) — actualmente 2
- `invader_cards_remaining` (int)
- `invader_cards_out_of_deck` (int)
- `dahan_alive` (int)
- `blight_on_island` (int)
- `score` (int, calculado al finalizar)

#### Exportación

- `exported` (bool)

Reglas:

- Solo **una Incursion activa** en toda la Era
- Orden libre dentro del Periodo
- `score` es inmutable tras finalizar

---

### Sessions (`sessions/{session_id}`)

- `started_at` (timestamp UTC)
- `ended_at` (timestamp | null)

Reglas:

- Múltiples sesiones por Incursion
- Solo una sesión abierta a la vez
- No se borran sesiones desde Android
- Duración total = suma de sesiones

---

## Reglas de escritura

### Generar Era (PC)

- Crea Era, Periodos e Incursions
- Solo setup base

### Revelar Periodo (Android)

- Fija `revealed_at`
- Asigna `adversary_id` a **todas las Incursiones del Periodo**

### Iniciar Incursion (Android)

- Fija `started_at`
- Asigna `adversary_level`
- Calcula y guarda `difficulty`

### Finalizar Incursion (Android)

- Fija `ended_at`
- Calcula y guarda `score`
- Finaliza Periodo si es la última Incursión pendiente

PC puede modificar cualquier campo sin restricciones.

---

## Navegación y vistas

1. Vista principal → Eras
2. Vista de Era → Periodos
3. Vista de Periodo → Incursions
4. Vista de Incursion → Sesiones y resultado

Reglas de UI:

- Navegación libre
- Estados indicados visualmente
- Acceso rápido a Incursion activa
- Restricción dura: no iniciar otra Incursion si hay una activa

---

## Puntuación

### Victoria

- `5 × difficulty`
- `+10`
- `+2 × invader_cards_remaining`

### Derrota

- `2 × difficulty`
- `+1 × invader_cards_out_of_deck`

### Siempre

- `+ player_count × dahan_alive`
- `− player_count × blight_on_island`

---

## Exportación TSV

Reglas:

- Una fila = Incursion finalizada
- Solo `ended_at != null`
- Archivo sobrescrito siempre
- Orden: Era → Periodo → Incursion
- Timestamps en **ISO 8601 UTC (Z)**

Columnas:

1. `era_id`
2. `period_index`
3. `incursion_index`
4. `spirit_1_id`
5. `spirit_2_id`
6. `board_1`
7. `board_2`
8. `board_layout`
9. `adversary_level`
10. `difficulty`
11. `player_count`
12. `result`
13. `invader_cards_remaining`
14. `invader_cards_out_of_deck`
15. `dahan_alive`
16. `blight_on_island`
17. `started_at`
18. `ended_at`
19. `duration_minutes`
20. `score`

---

## Estado del diseño

- Modelo: cerrado
- Reglas: cerradas
- Flujo: coherente
- Listo para implementación
