@echo off
echo =============================
echo   MAESTRO Service Launcher
echo =============================
echo 1. Start Dashboard (dashboard/app.py)
echo 2. Start Webhook Server (scripts/webhook_server.py)
echo 3. Exit
set /p choice="Select an option (1-3): "

if "%choice%"=="1" (
	echo Starting Dashboard...
	start "Dashboard" cmd /k "venv\Scripts\activate && cd dashboard && python app.py"
	goto :eof
)
if "%choice%"=="2" (
	echo Starting Webhook Server...
	start "Webhook Server" cmd /k "venv\Scripts\activate && python scripts\webhook_server.py"
	goto :eof
)
if "%choice%"=="3" (
	echo Exiting.
	exit /b
)
echo Invalid option. Exiting.
exit /b