@echo off
echo ===================================================
echo Launching LunarSynapse Scientific Platform
echo ===================================================

start "LunarSynapse Backend" cmd /k "call start_backend.bat"
timeout /t 3 /nobreak >nul
start "LunarSynapse Frontend" cmd /k "call start_frontend.bat"

echo.
echo Both servers launched.
echo Backend API Docs: http://127.0.0.1:8000/docs
echo Frontend Mission Control: http://localhost:5173
echo.
