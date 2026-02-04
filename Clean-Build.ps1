<#  Clean-Build.ps1  (Windows PowerShell 5.1 compatible)
    Borra la carpeta build (prioriza .\app\build) aunque haya locks típicos de Java/Gradle/Kotlin.
    Uso:
      powershell -ExecutionPolicy Bypass -File .\Clean-Build.ps1
#>

[CmdletBinding()]
param()

function Test-IsAdmin {
    $current = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($current)
    return $principal.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
}

function Relaunch-AsAdmin {
    $argList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$PSCommandPath`"")
    Start-Process -FilePath "powershell.exe" -ArgumentList $argList -Verb RunAs | Out-Null
    exit
}

function Pick-BuildPath {
    $cwd = (Get-Location).Path
    $scriptDir = Split-Path -Parent $PSCommandPath

    $candidates = @(
        (Join-Path $cwd "app\build"),
        (Join-Path $cwd "build"),
        (Join-Path $scriptDir "app\build"),
        (Join-Path $scriptDir "build")
    )

    foreach ($p in $candidates) {
        if (Test-Path -LiteralPath $p) { return $p }
    }

    # si no existe ninguno, devuelve el más probable igualmente
    return (Join-Path $cwd "app\build")
}

function Try-RemoveFolder {
    param([string]$PathToRemove)

    Write-Host "Intentando eliminar: $PathToRemove"

    if (-not (Test-Path -LiteralPath $PathToRemove)) {
        Write-Host "No existe (ok): $PathToRemove"
        return $true
    }

    # Quita atributos (solo para evitar bloqueos por readonly/system)
    try {
        Get-ChildItem -LiteralPath $PathToRemove -Recurse -Force -ErrorAction SilentlyContinue |
        ForEach-Object { try { $_.Attributes = 'Normal' } catch {} }
    }
    catch {}

    try {
        Remove-Item -LiteralPath $PathToRemove -Recurse -Force -ErrorAction Stop
        Write-Host "✅ Eliminado: $PathToRemove"
        return $true
    }
    catch {
        Write-Host "❌ Sigue bloqueado: $($_.Exception.Message)"
        return $false
    }
}

function Stop-ByName {
    param([string[]]$Names)

    foreach ($n in $Names) {
        Get-Process -Name $n -ErrorAction SilentlyContinue | ForEach-Object {
            try {
                Write-Host "Matando $($_.ProcessName) (PID $($_.Id))"
                Stop-Process -Id $_.Id -Force -ErrorAction Stop
            }
            catch {}
        }
    }
}

function Stop-ByCmdlineContains {
    param([string[]]$Needles)

    # Win32_Process da acceso a CommandLine
    try {
        $procs = Get-CimInstance Win32_Process -ErrorAction Stop
    }
    catch {
        $procs = @()
    }

    foreach ($p in $procs) {
        $cmd = $p.CommandLine
        if ([string]::IsNullOrWhiteSpace($cmd)) { continue }

        $hit = $false
        foreach ($needle in $Needles) {
            if ($cmd -like "*$needle*") { $hit = $true; break }
        }

        if ($hit) {
            try {
                Write-Host "Matando por cmdline: $($p.Name) (PID $($p.ProcessId))"
                Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
            }
            catch {}
        }
    }
}

function Try-GradleStop {
    param([string]$RepoRoot)

    $gradlewCandidates = @(
        (Join-Path $RepoRoot "gradlew.bat"),
        (Join-Path $RepoRoot "app\build\flutter\android\gradlew.bat"),
        (Join-Path $RepoRoot "app\build\flutter\gradlew.bat")
    )

    foreach ($g in $gradlewCandidates) {
        if (Test-Path -LiteralPath $g) {
            Write-Host "Ejecutando: $g --stop"
            try { & $g --stop | Out-Null } catch {}
        }
    }
}

# --- MAIN ---

if (-not (Test-IsAdmin)) { Relaunch-AsAdmin }

$repoRoot = (Get-Location).Path
$target = Pick-BuildPath

Write-Host "Repo:   $repoRoot"
Write-Host "Build:  $target"
Write-Host ""

# 1) intento directo
if (Try-RemoveFolder -PathToRemove $target) { exit 0 }

Write-Host ""
Write-Host "=== Parando procesos típicos (Flutter/Gradle/Java/Kotlin) ==="

# 2) corta lo obvio por nombre
Stop-ByName -Names @(
    "java", "javaw",
    "gradle", "kotlin-daemon", "kotlinc",
    "dart", "flutter", "adb"
)

# 3) corta por CommandLine (suele pillar el daemon correcto)
Stop-ByCmdlineContains -Needles @(
    "org.gradle",
    "GradleDaemon",
    "kotlin-daemon",
    "KotlinCompileDaemon",
    "flutter_tools",
    "\.gradle\",
    "shared_preferences_android",
    "lint",
    "androidx.lifecycle"
)

# 4) intenta parar gradle daemon si existe gradlew
Try-GradleStop -RepoRoot $repoRoot

Start-Sleep -Milliseconds 800

Write-Host ""
Write-Host "=== Reintentando borrado ==="

# 5) reintento
if (Try-RemoveFolder -PathToRemove $target) { exit 0 }

Write-Host ""
Write-Host "=== Último recurso: taskkill masivo a java/javaw (cierra builds/Android Studio) ==="

# 6) último recurso (más agresivo): taskkill con /T
try { & taskkill /F /IM java.exe /T  | Out-Null } catch {}
try { & taskkill /F /IM javaw.exe /T | Out-Null } catch {}
try { & taskkill /F /IM gradle.exe /T | Out-Null } catch {}
try { & taskkill /F /IM kotlin-daemon.exe /T | Out-Null } catch {}

Start-Sleep -Milliseconds 800

Write-Host ""
Write-Host "=== Reintento final de borrado ==="

if (Try-RemoveFolder -PathToRemove $target) { exit 0 }

Write-Host ""
Write-Host "❗ No se pudo borrar ni así."
Write-Host "   Causa típica: IDE abierto (Android Studio) o antivirus/indexador tocando el árbol."
Write-Host "   Prueba a cerrar Android Studio/VSCode/terminales que estén en esa carpeta y vuelve a ejecutar."
exit 1
