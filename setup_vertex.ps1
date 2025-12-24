$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Load-DotEnv([string]$path) {
  $kv = @{}
  if (!(Test-Path $path)) { return $kv }
  foreach ($line in Get-Content $path) {
    $t = $line.Trim()
    if (!$t -or $t.StartsWith("#")) { continue }
    if ($t -notmatch "=") { continue }
    $k, $v = $t.Split("=", 2)
    $k = $k.Trim()
    $v = $v.Trim().Trim('"')
    if ($k) { $kv[$k] = $v }
  }
  return $kv
}

function Get-GcloudPath() {
  try {
    $cmd = Get-Command gcloud -ErrorAction Stop
    return $cmd.Source
  } catch {
    $p = Join-Path $env:LocalAppData "Google\\Cloud SDK\\google-cloud-sdk\\bin\\gcloud.cmd"
    if (Test-Path $p) { return $p }
  }
  throw "gcloud not found. Install Google Cloud SDK or restart terminal."
}

$dotenv = Load-DotEnv (Join-Path $root ".env")
$projectId = $dotenv["GOOGLE_CLOUD_PROJECT"]
if (-not $projectId) {
  $projectId = Read-Host "Enter your GOOGLE_CLOUD_PROJECT (GCP project ID)"
}
if (-not $projectId) {
  throw "Missing GOOGLE_CLOUD_PROJECT."
}

$gcloud = Get-GcloudPath
Write-Host "Using gcloud: $gcloud" -ForegroundColor Gray

Write-Host ""
Write-Host "Setting active project to: $projectId" -ForegroundColor Cyan
& $gcloud config set project $projectId | Out-Host

Write-Host ""
Write-Host "Enabling Vertex AI API (aiplatform.googleapis.com)..." -ForegroundColor Cyan
& $gcloud services enable aiplatform.googleapis.com --project $projectId --quiet | Out-Host

Write-Host ""
Write-Host "Verifying Application Default Credentials (ADC)..." -ForegroundColor Cyan
try {
  $token = & $gcloud auth application-default print-access-token --quiet
  if (-not $token) { throw "Empty token" }
  Write-Host "- ADC token: OK" -ForegroundColor Green
} catch {
  Write-Host "- ADC token: FAILED" -ForegroundColor Red
  Write-Host "Run: gcloud auth application-default login" -ForegroundColor Yellow
  throw
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "- Next: run .\\preflight.ps1 then .\\start_demo.bat"

