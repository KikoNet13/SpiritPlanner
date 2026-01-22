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

#### Estado derivado

- `active_incursion` (object | null)
  - `period_id` (string)
  - `incursion_id` (string)

Reglas:

- `active_incursion` identifica la Incursión activa actual
- Se escribe al iniciar una Incursión
- Se elimina al finalizar una Incursión
- Es un estado derivado para optimización; Firestore sigue siendo la única fuente de verdad

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
- Un Periodo solo puede iniciarse tras haber sido revelado
- Una vez iniciado un Periodo, su configuración estratégica queda bloqueada

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

#### Asignación estratégica (tras revelar Periodo)

- `adversary_id` (string | null)

Reglas de asignación:

- Cada Incursión del Periodo debe tener un `adversary_id` asignado antes de iniciar el Periodo
- En un mismo Periodo:
  - deben existir exactamente **4 Incursiones**
  - las 4 deben tener `adversary_id` no nulo
  - los 4 `adversary_id` deben ser **distintos**
  - `"scenario"` cuenta como un adversario válido más
- Una vez el Periodo está iniciado (`started_at != null`), la asignación de adversarios queda **bloqueada**

#### Al iniciar la Incursión

- `adversary_level` (string | null)
- `difficulty` (int)

Notas:

- Los escenarios se tratan como adversarios
- El nivel es texto libre (ej. “Base”, “Nivel 3”, “Rituales de terror”)

#### Estado temporal

- `started_at` (timestamp | null)
- `ended_at` (timestamp | null)

Reglas:

- Solo puede existir **una Incursión activa** en toda la Era
- Las Incursiones de un Periodo pueden jugarse en cualquier orden

#### Score

- `result` (`"win"` / `"loss"`)
- `player_count` (int)
- `invader_cards_remaining` (int)
- `invader_cards_out_of_deck` (int)
- `dahan_alive` (int)
- `blight_on_island` (int)
- `score` (int)

Reglas:

- El score se calcula **al finalizar** la Incursión según la fórmula definida
- El score es **inmutable** tras finalizar

#### Exportación

- `exported` (bool)

---

### Sessions (`sessions/{session_id}`)

- `started_at` (timestamp UTC)
- `ended_at` (timestamp | null)

Reglas:

- Una Incursión puede tener múltiples sesiones
- Solo una sesión abierta a la vez
- No se borran sesiones desde Android
- La duración total es la suma de todas las sesiones

---

## Reglas de escritura

### Generar Era (PC)

- Crea Era, Periodos e Incursions
- Solo setup base (sin estado de juego)

### Revelar Periodo (Android)

- Fija `revealed_at`
- Habilita la asignación de adversarios a las Incursiones del Periodo

### Iniciar Incursión (Android)

- Valida que el Periodo está revelado
- Valida la asignación correcta de adversarios del Periodo
- Fija `started_at`
- Asigna `adversary_level`
- Calcula y guarda `difficulty`
- Registra la Incursión activa en la Era

### Finalizar Incursión (Android)

- Fija `ended_at`
- Calcula y guarda `score`
- Elimina la Incursión activa de la Era
- Finaliza el Periodo si es la última Incursión pendiente

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
- Restricción dura: no iniciar otra Incursión si hay una activa

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
