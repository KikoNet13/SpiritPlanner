# Documentación de SpiritPlanner

## 1) Visión general

SpiritPlanner es una herramienta para gestionar campañas en solitario de **Spirit Island** usando **Firestore** como fuente única de verdad. Permite organizar Eras, Periodos e Incursiones, registrar sesiones de tiempo y calcular puntuaciones finales. La UI principal está implementada en **Flet (Python)** y se apoya en Firestore para lectura/escritura.

**Qué problema resuelve**
- Centraliza el estado de la campaña (Eras → Periodos → Incursiones) y sus progresos.
- Facilita el control del tiempo por sesiones y el cálculo de puntuaciones.

**Tecnologías principales**
- **Flet** para la interfaz (Page, View, overlays y diálogos).
- **Firestore** como backend y fuente de verdad.
- Catálogos **TSV** (en `pc/data/input`) para nombres legibles de espíritus, tableros, adversarios y layouts.

**Qué NO hace la app (límites de alcance)**
- No define nuevas reglas de juego ni modifica el modelo de datos fuera del flujo descrito en README.
- No gestiona funcionalidades ajenas a Eras/Periodos/Incursiones, control de tiempo y puntuación.

## 2) Estructura del proyecto

Estructura relevante a alto nivel:

- `README.md`: especificación funcional y reglas de negocio (modelo de datos, flujo, puntuación, navegación).
- `app/`: aplicación Flet (UI y acceso a Firestore).
  - `main.py`: entrada principal, enrutamiento y composición de vistas.
  - `screens/`: vistas de UI (Eras, Periodos, Incursiones, Detalle).
  - `services/`: lógica de acceso a Firestore y cálculo de puntuación.
- `pc/`: utilidades de PC y datos auxiliares.
  - `data/input/`: catálogos TSV consumidos por la UI para nombres legibles.

## 3) Descripción por archivo (app)

### `app/main.py`
- **Qué representa**: punto de entrada de la app Flet.
- **Pantallas/clases/funciones**: `main(page)` configura `Page`, crea `FirestoreService` y define el enrutamiento dinámico basado en la ruta.
- **Responsabilidad**: orquesta la navegación y compone las vistas en la pila (`page.views`).
- **Tipo**: UI + router.

### `app/screens/eras_screen.py`
- **Qué representa**: vista principal de listado de Eras.
- **Pantallas/clases/funciones**: `eras_view(page, service)`.
- **Responsabilidad**: muestra Eras, estado (activa/inactiva) y acceso a Periodos; habilita acceso rápido a una incursión activa si existe.
- **Tipo**: UI.

### `app/screens/periods_screen.py`
- **Qué representa**: vista de Periodos dentro de una Era.
- **Pantallas/clases/funciones**: `periods_view(page, service, era_id)`, diálogos para revelar periodos y asignar adversarios.
- **Responsabilidad**: listar Periodos, permitir revelar el siguiente periodo, y asignar adversarios a cada Incursión antes de iniciar el periodo.
- **Tipo**: UI + validaciones de flujo (a través de `FirestoreService`).

### `app/screens/incursions_screen.py`
- **Qué representa**: vista de Incursiones de un Periodo.
- **Pantallas/clases/funciones**: `incursions_view(page, service, era_id, period_id)`.
- **Responsabilidad**: listar Incursiones con sus datos clave (espíritus, tableros, layout, adversario y estado) y navegar al detalle.
- **Tipo**: UI.

### `app/screens/incursion_detail_screen.py`
- **Qué representa**: detalle de una Incursión específica.
- **Pantallas/clases/funciones**: `incursion_detail_view(page, service, era_id, period_id, incursion_id)` y manejadores para iniciar, pausar/reanudar y finalizar.
- **Responsabilidad**:
  - Mostrar configuración y estado de la incursión.
  - Iniciar incursión con selección de nivel de adversario y cálculo de dificultad.
  - Pausar/reanudar sesiones y finalizar con captura de resultados.
  - Mostrar sesiones registradas y duración total.
- **Tipo**: UI + coordinación de flujo con Firestore.

### `app/screens/data_lookup.py`
- **Qué representa**: utilidades para obtener nombres legibles desde catálogos TSV.
- **Pantallas/clases/funciones**: `get_spirit_name`, `get_board_name`, `get_layout_name`, `get_adversary_catalog`, `get_adversary_levels`, `get_adversary_difficulty`.
- **Responsabilidad**: cargar datos TSV y resolver IDs técnicos a nombres mostrables y niveles de adversario.
- **Tipo**: utilidades/lectura de datos.

### `app/services/firestore_service.py`
- **Qué representa**: capa de acceso a Firestore y reglas de negocio básicas.
- **Pantallas/clases/funciones**: `FirestoreService` (listados, revelar periodos, asignar adversarios, iniciar/pausar/reanudar/finalizar incursiones, sesiones).
- **Responsabilidad**: aplicar reglas de estado de la campaña, validar restricciones (p. ej. periodo revelado, única incursión activa) y persistir cambios en Firestore.
- **Tipo**: servicio (backend client + lógica).

### `app/services/score_service.py`
- **Qué representa**: lógica aislada de cálculo de puntuación.
- **Pantallas/clases/funciones**: `calculate_score(...)`.
- **Responsabilidad**: encapsular la fórmula de score según resultado y métricas de la incursión.
- **Tipo**: utilidad/lógica de negocio.

### `app/__init__.py`, `app/screens/__init__.py`, `app/services/__init__.py`
- **Qué representan**: marcadores de paquete Python.
- **Responsabilidad**: permitir importaciones por módulo.
- **Tipo**: infraestructura.

## 4) Flujo general de la aplicación

### Flujo de navegación principal
1. **Eras** → lista de eras disponibles.
2. **Periodos** (dentro de una Era) → lista de periodos, con estado (no revelado / revelado / activo / finalizado).
3. **Incursiones** (dentro de un Periodo) → lista de incursiones con datos de configuración.
4. **Detalle de Incursión** → gestión de inicio, sesiones y finalización.

Este flujo está implementado por rutas (`/eras`, `/eras/{era_id}`, `/eras/{era_id}/periods/{period_id}`, `/eras/{era_id}/periods/{period_id}/incursions/{incursion_id}`) y su composición en la pila de vistas.

### Cuándo se revela un Periodo
- Un Periodo puede revelarse si el anterior está finalizado (secuencia estricta). Al revelarlo se habilita la asignación de adversarios para sus incursiones.

### Cómo se asignan adversarios
- La asignación se realiza tras revelar el periodo.
- Cada incursión del periodo debe tener un adversario y todos deben ser distintos antes de iniciar una incursión del periodo.

### Qué significa una Incursión activa
- Una incursión activa es aquella que está iniciada (`started_at`) y no finalizada (`ended_at`). Solo puede existir una incursión activa por Era.

### Relación con Firestore (alto nivel)
- Firestore almacena Eras, Periodos, Incursiones y Sesiones.
- La UI consulta listas (Eras/Periodos/Incursiones/Sesiones) y actualiza el estado (revelar periodo, iniciar/finalizar incursión, registrar sesiones).

## 5) Notas técnicas relevantes

- **Uso de Flet**: la app usa `Page`, `View` y navegación por rutas; los diálogos (`AlertDialog`) y `overlay` se emplean para acciones modales (revelar periodo, asignar adversarios, finalizar incursión).
- **Separación UI / lógica**: la UI vive en `app/screens` y la lógica de acceso y validación de reglas se centraliza en `FirestoreService`.
- **Catálogos TSV**: `app/screens/data_lookup.py` carga catálogos TSV desde `pc/data/input` para convertir IDs técnicos en nombres legibles en la interfaz.
