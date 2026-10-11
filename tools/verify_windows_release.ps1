param(
    [ValidateSet("100", "125")][string]$Scale = "125"
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$RepoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $RepoRoot
$OS = Get-CimInstance Win32_OperatingSystem
if ([int]$OS.BuildNumber -lt 22000 -or $OS.Caption -notmatch "Windows 11") {
    throw "This acceptance requires real Windows 11, not Windows Server CI."
}
if ($env:QT_SCALE_FACTOR -or $env:QT_SCREEN_SCALE_FACTORS) {
    throw "Remove Qt scale overrides and set Windows display scaling in Settings."
}
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$EvidenceRoot = Join-Path $RepoRoot "release-evidence/windows11-$Scale-$Stamp"
New-Item -ItemType Directory -Path $EvidenceRoot -Force | Out-Null
$env:QT_API = "pyside6"
$env:MPLBACKEND = "QtAgg"
$env:OMP_NUM_THREADS = "2"
$env:OPENBLAS_NUM_THREADS = "2"
$env:MKL_NUM_THREADS = "2"
$env:PYTHONUTF8 = "1"
# Separate logs for this run; do not mix with a previous application's crashes.
$env:LOCALAPPDATA = Join-Path $EvidenceRoot "local-appdata"
New-Item -ItemType Directory -Path $env:LOCALAPPDATA -Force | Out-Null

function Invoke-Checked {
    param([string]$Label, [string]$Program, [string[]]$CommandArgs)
    $Log = Join-Path $EvidenceRoot "$Label.log"
    Write-Host "Running $Label"
    & $Program @CommandArgs *> $Log
    if ($LASTEXITCODE -ne 0) {
        Get-Content $Log -Tail 80
        throw "$Label failed (exit $LASTEXITCODE); see $Log"
    }
}

py -3.12 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Install Python 3.12 with the py launcher first." }
$Python = Join-Path $RepoRoot ".venv/Scripts/python.exe"
Invoke-Checked "dependencies" $Python @("-m", "pip", "install", "-r", "requirements.txt", "pyinstaller==6.16.0")
Invoke-Checked "pip-check" $Python @("-m", "pip", "check")
Invoke-Checked "compile" $Python @("-m", "compileall", "-q", "main.py", "app", "core", "tests", "tools")
$env:QT_QPA_PLATFORM = "offscreen"
$env:MPLBACKEND = "Agg"
Invoke-Checked "all-tests" $Python @("-m", "pytest", "-q")
$env:QT_QPA_PLATFORM = "windows"
$env:MPLBACKEND = "QtAgg"
Invoke-Checked "native-pca-test" $Python @("-m", "pytest", "-q", "tests/test_pca_gui_rendering.py")
Invoke-Checked "source-startup" $Python @("main.py", "--self-check")
Invoke-Checked "source-pca-stress" $Python @("main.py", "--pca-gui-self-check")
Invoke-Checked "source-all-graphics" $Python @("main.py", "--graphics-gui-self-check")
$SourceOutput = Join-Path $EvidenceRoot "source"
Invoke-Checked "source-acceptance" $Python @("main.py", "--release-acceptance", "--acceptance-output", $SourceOutput)
$Facts = Get-Content (Join-Path $SourceOutput "evidence.json") -Raw | ConvertFrom-Json
$ExpectedRatio = [double]$Scale / 100
if (-not $Facts.native_windows_capture -or [math]::Abs($Facts.device_pixel_ratio - $ExpectedRatio) -gt 0.02) {
    throw "Actual Qt DPI does not match Windows $Scale% scaling. Check the display Settings and rerun."
}
# Measure cold/warm process startup without imposing an invented speed target.
$TimingCode = @'
import json, subprocess, sys, time
elapsed=[]
for _ in range(3):
    started=time.perf_counter()
    subprocess.run([sys.argv[1], '--self-check'], check=True, timeout=180)
    elapsed.append(round(time.perf_counter()-started, 3))
print(json.dumps({'startup_seconds':elapsed}))
'@
$Dist = Join-Path $EvidenceRoot "dist"
$Build = Join-Path $EvidenceRoot "build"
Invoke-Checked "pyinstaller" $Python @("-m", "PyInstaller", "--noconfirm", "--clean", "--distpath", $Dist, "--workpath", $Build, "HighDimClusterSystem.spec")
$Bundle = Join-Path $Dist "HighDimClusterSystem"
Invoke-Checked "dll-integrity" $Python @("-m", "tools.verify_release", "--original", $Bundle)
$Downloaded = Join-Path $EvidenceRoot "transferred"
Copy-Item $Bundle $Downloaded -Recurse
Invoke-Checked "transfer-and-startup" $Python @("-m", "tools.verify_release", "--original", $Bundle, "--downloaded", $Downloaded)
$Exe = Join-Path $Downloaded "HighDimClusterSystem.exe"
$SavedPythonPath = $env:PYTHONPATH
$SavedPythonHome = $env:PYTHONHOME
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
$RunExeCode = "import subprocess,sys; subprocess.run(sys.argv[1:],check=True,timeout=900)"
try {
    Invoke-Checked "exe-startup-timing" $Python @("-c", $TimingCode, $Exe)
    Invoke-Checked "exe-pca-stress" $Python @("-c", $RunExeCode, $Exe, "--pca-gui-self-check")
    Invoke-Checked "exe-all-graphics" $Python @("-c", $RunExeCode, $Exe, "--graphics-gui-self-check")
    $ExeOutput = Join-Path $EvidenceRoot "exe"
    Invoke-Checked "exe-acceptance" $Python @("-c", $RunExeCode, $Exe, "--release-acceptance", "--acceptance-output", $ExeOutput)
} finally {
    if ($null -ne $SavedPythonPath) { $env:PYTHONPATH = $SavedPythonPath }
    if ($null -ne $SavedPythonHome) { $env:PYTHONHOME = $SavedPythonHome }
}
if ((Test-Path (Join-Path $RepoRoot ".git")) -and (Get-Command git -ErrorAction SilentlyContinue)) {
    $GitCommit = git rev-parse HEAD
    if ($LASTEXITCODE -ne 0) { throw "Cannot record source commit." }
    $GitStatus = @(git status --short)
} elseif (Test-Path (Join-Path $RepoRoot "SOURCE_COMMIT.txt")) {
    $GitCommit = (Get-Content (Join-Path $RepoRoot "SOURCE_COMMIT.txt") -Raw).Trim()
    $GitStatus = @("Source archive; Git status unavailable")
} else {
    throw "Use the delivered source archive with SOURCE_COMMIT.txt, or a Git checkout."
}
$Manifest = @{
    os = $OS.Caption; build = $OS.BuildNumber; commit = $GitCommit
    git_status = @($GitStatus); requested_scale = $Scale
    visual_review = "pending human screenshot inspection"
    transfer_check = "local copy; GitHub upload/download requires its separate workflow"
    status = "automated checks passed; manual Windows visual acceptance pending"
}
$Manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $EvidenceRoot "windows-run.json") -Encoding UTF8
Write-Host "Evidence: $EvidenceRoot"
Write-Host "Inspect source and EXE PNGs for Chinese glyphs, truncation and overflow."
Write-Host "Keep the window unobscured during screenshots. Return logs, JSONs and PNGs."
