# SpiritPlanner — Comandos típicos (Windows / PowerShell)

Este documento es un “chuletario” de comandos frecuentes para desarrollo, pruebas en Android y tooling PC.

## Reglas rápidas

- Ejecuta los comandos **desde la raíz del repo**, salvo que se indique lo contrario.
- Entorno: `pipenv`.
- El `.exe` de tooling PC es **local** (no se commitea).
- Firestore requiere credenciales: `GOOGLE_APPLICATION_CREDENTIALS`.

## 1) Preparar el entorno

Instalar dependencias (incluye dev):

```powershell
pipenv install --dev
```

Verificar versiones:

```powershell
python --version
python -c "import flet; print(flet.__version__)"
```

## 2) Credenciales Firestore (ADC)

### 2.1) Desarrollo (repo root)

Archivo `.env` en la raíz del repo:

```env
GOOGLE_APPLICATION_CREDENTIALS=D:\Proyectos\Python\Juegos de mesa\Spirit Island\spiritplanner-firebase-admin.json
SPIRITPLANNER_DEBUG=1
```

Verificar desde PowerShell:

```powershell
python -c "import os; print(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))"
```

### 2.2) Tooling PC compilado (doble click)

Archivo `tools\.env` (misma carpeta que `tools\spiritplanner.exe`):

```env
GOOGLE_APPLICATION_CREDENTIALS=D:\Proyectos\Python\Juegos de mesa\Spirit Island\spiritplanner-firebase-admin.json
SPIRITPLANNER_DEBUG=1
```

Notas:

- Asegúrate de que el fichero se llama exactamente `.env` (no `.env.txt`).
- El path del JSON debe existir.

## 3) Ejecutar la app (PC / escritorio)

Ejecutar en modo desktop:

```powershell
flet run app\main.py
```

## 4) Probar en Android (modo “server + QR”)

Requisitos:

- Tener instalada la app “Flet” en Android (Play Store).
- PC y móvil en la **misma red local**.

Arrancar servidor de desarrollo (aparece QR en la terminal):

```powershell
flet run --android app\main.py
```

Pasos en el móvil:

1. Abrir la app Flet.
2. Escanear el QR que aparece en la terminal del PC.
3. Se abrirá el proyecto y se actualizará al guardar cambios (hot reload).

Volver a “Home” en la app Flet:

- Mantén pulsado con 3 dedos, o
- Agita el dispositivo.

## 5) Build Android (APK / AAB)

Generar APK release:

```powershell
flet build apk . --module-name "main" --product "SpiritPlanner"
```

Generar AAB release (Play Store):

```powershell
flet build aab . --module-name "main" --product "SpiritPlanner"
```

Logs verbosos (si algo falla):

```powershell
flet build apk -vv . --module-name "main" --product "SpiritPlanner"
```

## 6) Tooling PC (menú interactivo) — modo Python

Ejecutar la herramienta PC sin compilar:

```powershell
python -m pc.spiritplanner_cli
```

## 7) Compilar tooling PC a .exe (PyInstaller → tools\)

### 7.1) Instalar PyInstaller si falta

```powershell
pyinstaller --version
```

Si falla:

```powershell
pipenv install --dev pyinstaller
```

### 7.2) Compilar el .exe en tools\

```powershell
pyinstaller -F pc\spiritplanner_cli.py -n spiritplanner --clean --distpath tools --workpath build\pyinstaller --specpath build\pyinstaller
```

Ejecutar:

```powershell
.\tools\spiritplanner.exe
```

## 8) Limpieza de artefactos de build

Borrar temporales de PyInstaller (sin borrar el .exe):

```powershell
Remove-Item -Recurse -Force .\build\pyinstaller -ErrorAction SilentlyContinue
```

## 9) Logs (rápido)

Si existe carpeta `logs\` y archivos tipo `spiritplanner-*.log`, abrir el último:

```powershell
$log = (Get-ChildItem .\logs\spiritplanner-*.log | Sort-Object LastWriteTime | Select-Object -Last 1).FullName
notepad $log
```
