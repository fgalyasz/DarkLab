$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$version = (Get-Content -Raw "$root\docs\version.txt").Trim()
$dist = Join-Path $root "dist"
$archive = Join-Path $dist "DarkLab-windows-x64.zip"

Set-Location $root
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller `
  --noconfirm `
  --windowed `
  --name DarkLab `
  --collect-binaries pyexiv2 `
  --distpath $dist `
  --workpath (Join-Path $root "build\pyinstaller") `
  main.py
if (Test-Path $archive) { Remove-Item -Force $archive }
Compress-Archive -Path (Join-Path $dist "DarkLab") -DestinationPath $archive
Write-Output "OK: $archive (version $version)"
