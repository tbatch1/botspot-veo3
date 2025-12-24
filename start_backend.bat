@echo off
chcp 65001
set PYTHONIOENCODING=utf-8

set "ROOT=%~dp0"
set "VENV_PY=%ROOT%.venv\Scripts\python.exe"
cd /d "%ROOT%"

REM Ensure ffmpeg is available even if PATH refresh hasn't propagated yet.
where ffmpeg >nul 2>&1
if errorlevel 1 (
  set "FFMPEG_DIR="
  for /f "delims=" %%F in ('dir /b /s "%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_*\\ffmpeg-*\\bin\\ffmpeg.exe" 2^>nul') do (
    set "FFMPEG_DIR=%%~dpF"
    goto :ffmpeg_found
  )
  :ffmpeg_found
  if defined FFMPEG_DIR (
    set "PATH=%FFMPEG_DIR%;%PATH%"
  )
)

if exist "%VENV_PY%" (
  "%VENV_PY%" -m uvicorn ott_ad_builder.api:app --host 0.0.0.0 --port 4000 --reload
) else (
  python -m uvicorn ott_ad_builder.api:app --host 0.0.0.0 --port 4000 --reload
)
