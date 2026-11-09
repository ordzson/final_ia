[CmdletBinding()]
param(
    [string]$PythonExe = "python.exe"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Python {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python fallo con codigo $LASTEXITCODE. La instalacion se detuvo."
    }
}

if ($env:OS -ne "Windows_NT") {
    throw "Este instalador es para Windows. En Linux usa ./setup.sh."
}

$VersionCheck = "import sys, struct; ok = sys.version_info[:2] == (3, 12) and struct.calcsize('P') == 8; print(sys.version); raise SystemExit(0 if ok else 'Se necesita Python 3.12 de 64 bits.')"
$VenvDirectory = Join-Path $PSScriptRoot ".venv"
$VenvPython = Join-Path $VenvDirectory "Scripts\python.exe"
$WindowsLock = Join-Path $PSScriptRoot "requirements.windows.lock.txt"
$CpuIndex = "https://download.pytorch.org/whl/cpu"
$OpenCvRequirement = "opencv-contrib-python-headless"

Push-Location -LiteralPath $PSScriptRoot
try {
    if (-not (Test-Path -LiteralPath $VenvDirectory)) {
        Invoke-Python -Executable $PythonExe -Arguments @("-c", $VersionCheck)
        Invoke-Python -Executable $PythonExe -Arguments @("-m", "venv", $VenvDirectory)
    }
    if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
        throw "La carpeta .venv existente no contiene un entorno de Windows. Conserva o renombra ese entorno antes de ejecutar setup.ps1."
    }
    Invoke-Python -Executable $VenvPython -Arguments @("-c", $VersionCheck)
    Invoke-Python -Executable $VenvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip")

    if (Test-Path -LiteralPath $WindowsLock -PathType Leaf) {
        # El lock de Windows conserva versiones verificadas, incluidas las ruedas CPU.
        $OpenCvPins = @(Get-Content -LiteralPath $WindowsLock | Where-Object {
            $_ -match '^opencv-contrib-python-headless==[^\s;]+$'
        })
        if ($OpenCvPins.Count -ne 1) {
            throw "requirements.windows.lock.txt debe fijar una sola version de opencv-contrib-python-headless."
        }
        $OpenCvRequirement = $OpenCvPins[0].Trim()
        Invoke-Python -Executable $VenvPython -Arguments @(
            "-m", "pip", "install", "-r", $WindowsLock, "--extra-index-url", $CpuIndex
        )
    }
    else {
        Invoke-Python -Executable $VenvPython -Arguments @(
            "-m", "pip", "install", "torch", "torchvision", "--index-url", $CpuIndex
        )
        Invoke-Python -Executable $VenvPython -Arguments @(
            "-m", "pip", "install", "-r", (Join-Path $PSScriptRoot "requirements.txt")
        )
    }

    # Ultralytics puede traer OpenCV con GUI; Qt se ejecuta mediante PySide6.
    Invoke-Python -Executable $VenvPython -Arguments @(
        "-m", "pip", "uninstall", "-y", "opencv-python", "opencv-contrib-python",
        "opencv-python-headless", "opencv-contrib-python-headless"
    )
    Invoke-Python -Executable $VenvPython -Arguments @("-m", "pip", "install", $OpenCvRequirement)
    Invoke-Python -Executable $VenvPython -Arguments @(
        "-c", "import cv2, mediapipe, ultralytics, openvino, PySide6; print('Dependencias OK')"
    )

    Write-Host "Instalacion lista. La camara integrada de este equipo usa el indice 1; puede cambiar en otros equipos. Usa el selector si hace falta."
    Write-Host '.\.venv\Scripts\python.exe app.py --camera 1'
}
finally {
    Pop-Location
}
