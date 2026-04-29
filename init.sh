#!/bin/bash
# Maestro-AI startup script: installs dependencies, verifies baseline, prints start command

# === EDIT THESE VARIABLES FOR YOUR PROJECT ===
INSTALL_CMD="pip install -r requirements.txt"
VERIFY_CMD="python test_agents.py"
START_CMD="python webhook_server.py"
# ============================================

set -e

# Print current directory
pwd

echo "[maestro-ai] Installing dependencies..."
$INSTALL_CMD

echo "[maestro-ai] Running verification..."
$VERIFY_CMD

echo "[maestro-ai] Startup verification complete."
echo "[maestro-ai] To start the dev server, run: $START_CMD"

if [ "$RUN_START_COMMAND" = "1" ]; then
  echo "[maestro-ai] RUN_START_COMMAND=1 detected. Starting dev server..."
  exec $START_CMD
fi
