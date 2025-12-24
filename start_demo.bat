@echo off
setlocal

set "ROOT=%~dp0"

start "OTT Backend (FastAPI)" cmd /k "%ROOT%start_backend.bat"
start "OTT Frontend (Next.js :3001)" cmd /k "cd /d \"%ROOT%frontend_new\" && npm run dev -- -p 3001"
