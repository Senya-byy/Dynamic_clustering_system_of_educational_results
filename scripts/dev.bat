@echo off
setlocal enabledelayedexpansion

set ROOT=%~dp0..
set BACKEND_DIR=%ROOT%\backend
set FRONTEND_DIR=%ROOT%\frontend

set BACKEND_PORT=5001
set FRONTEND_PORT=5173

echo Backend port: %BACKEND_PORT%
echo Frontend port: %FRONTEND_PORT%

echo.
echo === LAN IP (Windows) ===
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
  set IP=%%a
)
set IP=%IP: =%
if "%IP%"=="" set IP=127.0.0.1
echo LAN IP: %IP%
echo Frontend LAN URL: http://%IP%:%FRONTEND_PORT%
echo Backend  LAN URL: http://%IP%:%BACKEND_PORT%
echo.

echo === Start backend ===
start "backend" cmd /c "cd /d "%BACKEND_DIR%" && set PYTHONPATH=. && set PORT=%BACKEND_PORT% && python app.py"

echo === Start frontend ===
start "frontend" cmd /c "cd /d "%FRONTEND_DIR%" && set VITE_PROXY_TARGET=http://127.0.0.1:%BACKEND_PORT% && npm run dev -- --host 0.0.0.0 --port %FRONTEND_PORT%"

echo.
echo ✅ Started. Close backend/frontend windows to stop.
endlocal

