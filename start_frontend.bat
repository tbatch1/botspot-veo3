@echo off
setlocal

set "ROOT=%~dp0"
cd /d "%ROOT%frontend_new" || exit /b 1

npm run dev -- -p 3001
