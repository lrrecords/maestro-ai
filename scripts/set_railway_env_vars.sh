#!/bin/bash
# Script to set environment variables for Railway using the Railway CLI
# Usage: ./set_railway_env_vars.sh <project_id> <maestro_token> [secret_key] [premium_features_enabled]

# Check for Railway CLI
if ! command -v railway &> /dev/null; then
  echo "Railway CLI not found. Install it from https://docs.railway.app/develop/cli" >&2
  exit 1
fi

PROJECT_ID="$1"
MAESTRO_TOKEN="$2"
SECRET_KEY="${3:-}"
PREMIUM_FEATURES_ENABLED="${4:-true}"

if [ -z "$PROJECT_ID" ] || [ -z "$MAESTRO_TOKEN" ]; then
  echo "Usage: $0 <project_id> <maestro_token> [secret_key] [premium_features_enabled]" >&2
  exit 1
fi

echo "Setting MAESTRO_TOKEN..."
railway variables set MAESTRO_TOKEN="$MAESTRO_TOKEN" --project "$PROJECT_ID"

if [ -n "$SECRET_KEY" ]; then
  echo "Setting SECRET_KEY..."
  railway variables set SECRET_KEY="$SECRET_KEY" --project "$PROJECT_ID"
fi

echo "Setting PREMIUM_FEATURES_ENABLED..."
railway variables set PREMIUM_FEATURES_ENABLED="$PREMIUM_FEATURES_ENABLED" --project "$PROJECT_ID"

echo "All variables set. Trigger a redeploy from the Railway dashboard if needed."
