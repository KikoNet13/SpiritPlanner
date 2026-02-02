# Board Layout Calibrator

Herramienta one-shot en Flet para calibrar `translate / rotate` de dos slots de tablero (`left` y `right`) sobre una imagen guia de layout.

## Ejecutar

- `pipenv run flet run .\tools\board_layout_calibrator\main.py`

## Imagenes guia

- Coloca las imagenes guia en `tools/board_layout_calibrator/assets/layouts/`.
- Nombre esperado por layout: `<layout_id>.png`.
- Layout IDs hardcoded: `alternating_shores`, `coastline`, `opposite_shores`, `sunrise_fragment`, `circle_fragment`.
- Si falta la imagen de un layout, la app sigue funcionando y muestra el aviso correspondiente.

## calibration.json

- Archivo generado en: `tools/board_layout_calibrator/calibration.json`.
- Se guarda solo el layout seleccionado y se preservan los demas.
- El viewport usa ratio fijo `16:9`.
- Formato:

```json
{
  "schema_version": 1,
  "layouts": {
    "alternating_shores": {
      "left": {
        "dx": -0.45,
        "dy": 0.0,
        "rot_deg": 0.0
      },
      "right": {
        "dx": 0.45,
        "dy": 0.0,
        "rot_deg": 0.0
      }
    }
  }
}
```
