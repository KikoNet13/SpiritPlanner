# Force UTF-8 console output (fix Rich/Flet CLI Unicode on Windows)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8NoBom
[Console]::InputEncoding  = $utf8NoBom
$OutputEncoding           = $utf8NoBom
$env:PYTHONIOENCODING     = "utf-8"

# For legacy codepage consumers
chcp 65001 | Out-Null

# tools/Clean-Build.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Ir al root del repo (carpeta del script -> subir un nivel si lo guardas en /tools)
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $repoRoot
try {
    # (Opcional) entrar al venv solo para el resto del script: NO recomendado con pipenv shell
    # Mejor: pipenv run <comando>

    # Parar procesos que a veces se quedan pillados (puede requerir permisos)
    Get-Process java, kotlin, gradle, dart, flutter -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

    # Limpiar build anterior
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue ".\app\build"

    # Build APK (mantén "app" si necesitas especificar la app del proyecto)
    pipenv run flet build apk app --clear-cache --no-android-splash

}
finally {
    Pop-Location
}
