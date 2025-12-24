$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "== Botspot Veo3 Demo Preflight ==" -ForegroundColor Cyan

function Test-EnvValue([string]$key, [hashtable]$kv) {
  if ($kv.ContainsKey($key) -and $kv[$key]) { return $true }
  $val = [Environment]::GetEnvironmentVariable($key, "Process")
  if ($val) { return $true }
  $val = [Environment]::GetEnvironmentVariable($key, "User")
  if ($val) { return $true }
  $val = [Environment]::GetEnvironmentVariable($key, "Machine")
  if ($val) { return $true }
  return $false
}

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

$dotenvPath = Join-Path $root ".env"
$dotenv = Load-DotEnv $dotenvPath

Write-Host ""
Write-Host "Env file: $dotenvPath" -ForegroundColor Gray
Write-Host ("- .env present: " + (Test-Path $dotenvPath))

$required = @("OPENAI_API_KEY", "FAL_API_KEY", "ELEVENLABS_API_KEY")
Write-Host ""
Write-Host "Required keys" -ForegroundColor Cyan
foreach ($k in $required) {
  $ok = Test-EnvValue $k $dotenv
  Write-Host ("- {0}: {1}" -f $k, ($(if ($ok) { "OK" } else { "MISSING" })))
}

$googleCreds = $null
if ($dotenv.ContainsKey("GOOGLE_APPLICATION_CREDENTIALS") -and $dotenv["GOOGLE_APPLICATION_CREDENTIALS"]) {
  $googleCreds = $dotenv["GOOGLE_APPLICATION_CREDENTIALS"]
} else {
  $googleCreds = [Environment]::GetEnvironmentVariable("GOOGLE_APPLICATION_CREDENTIALS", "Process")
}

Write-Host ""
Write-Host "Google / Vertex (Veo)" -ForegroundColor Cyan
if ($googleCreds) {
  $resolved = $googleCreds
  if (!(Split-Path $googleCreds -IsAbsolute)) {
    $resolved = Join-Path $root $googleCreds
  }
  Write-Host ("- GOOGLE_APPLICATION_CREDENTIALS set: OK")
  Write-Host ("- Credentials file exists: " + (Test-Path $resolved))
} else {
  $adcPath = Join-Path $env:APPDATA "gcloud\\application_default_credentials.json"
  Write-Host ("- GOOGLE_APPLICATION_CREDENTIALS set: NO (using ADC instead)")
  Write-Host ("- ADC file exists: " + (Test-Path $adcPath))
  Write-Host ("  If false, run: gcloud auth application-default login")
}

$project = $dotenv["GOOGLE_CLOUD_PROJECT"]
if (!$project) { $project = [Environment]::GetEnvironmentVariable("GOOGLE_CLOUD_PROJECT", "Process") }
Write-Host ("- GOOGLE_CLOUD_PROJECT set: " + ($(if ($project) { "OK" } else { "MISSING (recommended)" })))

Write-Host ""
Write-Host "Local tools" -ForegroundColor Cyan
$venvPy = Join-Path $root ".venv\\Scripts\\python.exe"
Write-Host ("- venv python: " + ($(if (Test-Path $venvPy) { "OK" } else { "MISSING (.venv not created)" })))

try {
  $ff = Get-Command ffmpeg -ErrorAction Stop
  Write-Host ("- ffmpeg: OK (" + $ff.Source + ")")
} catch {
  $ffmpegFound = $false
  $ffmpegRoot = Join-Path $env:LocalAppData "Microsoft\\WinGet\\Packages"
  if (Test-Path $ffmpegRoot) {
    $pkg = Get-ChildItem -Directory $ffmpegRoot -Filter "Gyan.FFmpeg_*" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($pkg) {
      $bin = Get-ChildItem -Path $pkg.FullName -Directory -Filter "ffmpeg-*" -ErrorAction SilentlyContinue |
        ForEach-Object { Join-Path $_.FullName "bin\\ffmpeg.exe" } |
        Where-Object { Test-Path $_ } |
        Select-Object -First 1
      if ($bin) {
        Write-Host ("- ffmpeg: FOUND (not on PATH yet) -> " + $bin) -ForegroundColor Yellow
        $ffmpegFound = $true
      }
    }
  }
  if (-not $ffmpegFound) {
    Write-Host "- ffmpeg: NOT FOUND" -ForegroundColor Yellow
  }
}

try {
  $gc = Get-Command gcloud -ErrorAction Stop
  Write-Host ("- gcloud: OK (" + $gc.Source + ")")
} catch {
  $gcloudPath = Join-Path $env:LocalAppData "Google\\Cloud SDK\\google-cloud-sdk\\bin\\gcloud.cmd"
  if (Test-Path $gcloudPath) {
    Write-Host ("- gcloud: FOUND (not on PATH yet) -> " + $gcloudPath) -ForegroundColor Yellow
  } else {
    Write-Host "- gcloud: NOT FOUND" -ForegroundColor Yellow
  }
}

Write-Host ""
Write-Host "Next" -ForegroundColor Cyan
Write-Host "- Start both: .\\start_demo.bat"
Write-Host "- Backend docs: http://localhost:4000/docs"
Write-Host "- Frontend:     http://localhost:3001"
