# SpiritPlanner — Documentación técnica

## 1) Visión general del proyecto
SpiritPlanner es una aplicación en Python con Flet y Firestore para gestionar eras, periodos, incursiones y sesiones. Firestore es la única fuente de verdad. La UI se construye de forma declarativa y la lógica se organiza por pantalla para facilitar lectura y edición.

## 2) Principios de diseño aplicados
- **SRP**: cada fichero responde a una sola pregunta.
- **Separación de responsabilidades**: UI, estado derivado y efectos están separados.
- **KISS**: funciones simples, sin abstracciones innecesarias.
- **DRY con moderación**: reutilización solo cuando aporta claridad.
- **Explícito sobre implícito**: estados y decisiones visibles.
- **Firestore como fuente de verdad**: sin cachés ni estados duplicados.

## 3) Estructura de carpetas (explicada)
```
app/
├─ main.py
├─ screens/
│  ├─ shared_components.py
│  ├─ eras/
│  │  ├─ eras_screen.py
│  │  ├─ eras_state.py
│  │  ├─ eras_handlers.py
│  │  ├─ eras_components.py
│  ├─ periods/
│  │  ├─ periods_screen.py
│  │  ├─ periods_state.py
│  │  ├─ periods_handlers.py
│  │  ├─ periods_components.py
│  ├─ incursions/
│  │  ├─ incursions_screen.py
│  │  ├─ incursions_state.py
│  │  ├─ incursions_handlers.py
│  │  ├─ incursions_components.py
│  ├─ incursion_detail/
│  │  ├─ incursion_detail_screen.py
│  │  ├─ incursion_detail_state.py
│  │  ├─ incursion_detail_handlers.py
│  │  ├─ incursion_detail_components.py
│  └─ data_lookup.py
├─ services/
├─ utils/
```

## 4) Flujo general de la app
1. `main.py` enruta las vistas por URL.
2. Cada pantalla carga datos desde Firestore mediante *handlers*.
3. El estado derivado se calcula en `*_state.py`.
4. La UI se compone en `*_screen.py` con componentes reutilizables.

## 5) Responsabilidad de cada tipo de fichero
- `*_screen.py`: composición UI, fácil de leer y sin reglas complejas.
- `*_state.py`: funciones puras de cálculo de estado y permisos.
- `*_handlers.py`: efectos (Firestore, navegación, mensajes).
- `*_components.py`: componentes visuales reutilizables de esa pantalla.
- `shared_components.py`: componentes visuales comunes a toda la app.

## 6) Cómo modificar
### UI
- Edita `*_screen.py` o `*_components.py`.
- Mantén textos visibles en castellano.

### Reglas
- Edita `*_state.py`.
- No añadas Flet ni acceso a Firestore.

### Handlers
- Edita `*_handlers.py`.
- Mantén efectos y llamadas a Firestore en este archivo.

## 7) Qué NO hacer (reglas del proyecto)
- No introducir clases de dominio con estado.
- No duplicar datos de Firestore en cachés locales.
- No crear capas adicionales (DDD, MVC clásico, Clean Architecture).
- No cambiar nombres de campos en Firestore.
- No mezclar lógica de negocio con UI.
