@echo off
echo Starting MAESTRO services...
start "Webhook Server" cmd /k "venv\Scripts\activate && python scripts\webhook_server.py"
echo Webhook server started on port 5678