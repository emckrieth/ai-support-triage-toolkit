$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python -m app.triage `
  --input data/sample_incidents.json `
  --runbooks runbooks `
  --output output/triage-results.json `
  --summary output/support-summary.md

python -m unittest discover -s tests

Write-Host ""
Write-Host "Demo complete."
Write-Host "Start the dashboard with: python -m http.server 8000"
Write-Host "Then open: http://localhost:8000/dashboard/"
