# ADR 0005 - MVVM declarativo en Flet con observable

Status: Accepted

## Contexto

La UI Flet necesitaba un contrato mas estricto para separar estado, efectos y vistas.
La llegada de `@ft.component` (hooks) y `@ft.observable` permite un patron MVVM declarativo real,
con estado observable y vistas derivadas sin mutaciones directas de controles.

## Decision

- Cada pantalla se organiza en tres archivos:
  - `*_model.py`: dataclasses de dominio/DTO para la vista.
  - `*_viewmodel.py`: ViewModel `@ft.observable` con estado y efectos.
  - `*_view.py`: componentes `@ft.component` que renderizan desde el ViewModel.
- La vista invoca metodos del ViewModel para cargar datos, disparar efectos y mutar estado.
- Los datos se cargan desde Firestore en el ViewModel y se reflejan por reactividad.
- Dialogos y snackbars se muestran con `page.show_dialog()` y se cierran con `page.pop_dialog()`.
- Se evita `page.update()` salvo overlays/navegacion; los cambios de estado deben disparar re-render.

## Consecuencias

- Estructura uniforme por pantalla y menos acoplamiento UI/efectos.
- Menos mutaciones de controles y mas trazabilidad de estado.
- Cambios en el patron requieren actualizar esta ADR y el TDD.

## Referencias

- `adr/0002-flet-declarative-ui-contract.md` (superseded)
- `app/main.py`
