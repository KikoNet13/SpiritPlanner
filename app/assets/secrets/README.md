# Credenciales Firebase (service account)

Coloca aquí el JSON de la service account que usará Firebase Admin SDK en la app empaquetada.

- Ruta esperada: `app/assets/secrets/service_account.json`
- Ejemplo (NO válido): `app/assets/secrets/service_account.json.example`

Importante: este fichero **no debe commitearse** (está ignorado en `.gitignore`), pero debe existir en tu máquina al ejecutar `flet build apk app` para que se empaquete dentro del APK.
