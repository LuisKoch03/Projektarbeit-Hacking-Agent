$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Virtuelle Umgebung fehlt: $python"
}

# PyInstaller must be able to read Tcl/Tk through Tcl itself. On some managed
# Windows installations the library under the user profile is visible to
# Python but not readable by Tcl. A local build copy avoids producing an EXE
# that starts with "No module named 'tkinter'".
$pythonBase = (& $python -c "import sys; print(sys.base_prefix)").Trim()
$tclSource = Join-Path $pythonBase "tcl"
$tclRuntime = Join-Path $PSScriptRoot "build\tcl-runtime"
$tclLibrary = Join-Path $tclRuntime "tcl8.6"
$tkLibrary = Join-Path $tclRuntime "tk8.6"

if (-not (Test-Path (Join-Path $tclSource "tcl8.6\init.tcl")) -or
    -not (Test-Path (Join-Path $tclSource "tk8.6\tk.tcl"))) {
    throw "Die Python-Installation enthält keine vollständige Tcl/Tk-Laufzeit."
}

New-Item -ItemType Directory -Force $tclLibrary, $tkLibrary | Out-Null
Copy-Item (Join-Path $tclSource "tcl8.6\*") $tclLibrary -Recurse -Force
Copy-Item (Join-Path $tclSource "tk8.6\*") $tkLibrary -Recurse -Force
$env:TCL_LIBRARY = $tclLibrary
$env:TK_LIBRARY = $tkLibrary

& $python -c "import tkinter as tk; root = tk.Tk(); root.withdraw(); root.destroy()"
if ($LASTEXITCODE -ne 0) {
    throw "Tkinter konnte nicht initialisiert werden. Die EXE wird nicht gebaut."
}

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --windowed `
    --name HackingAgent `
    --paths (Join-Path $PSScriptRoot "src") `
    --collect-all langchain `
    --collect-all langchain_core `
    --collect-all langchain_openai `
    (Join-Path $PSScriptRoot "launcher_gui.py")

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller ist mit Exit-Code $LASTEXITCODE fehlgeschlagen."
}

$target = Join-Path $PSScriptRoot "dist\HackingAgent"
Copy-Item "$PSScriptRoot\compose.yaml" $target -Force
Copy-Item "$PSScriptRoot\Dockerfile.nmap" $target -Force
Copy-Item "$PSScriptRoot\Dockerfile.hashcat" $target -Force
Copy-Item "$PSScriptRoot\.env.example" "$target\.env" -Force

$envPath = Join-Path $target ".env"
$zapKey = [guid]::NewGuid().ToString("N")
(Get-Content $envPath -Raw).Replace("ZAP_API_KEY=change-me", "ZAP_API_KEY=$zapKey") |
    Set-Content $envPath -Encoding utf8

New-Item -ItemType Directory -Force "$target\hashcat-work" | Out-Null
if (Test-Path "$PSScriptRoot\wordlists") {
    Copy-Item "$PSScriptRoot\wordlists" "$target\wordlists" -Recurse -Force
}

Write-Host "Fertig: $target\HackingAgent.exe"
