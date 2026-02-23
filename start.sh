#!/bin/bash
set -e

# Start the prospect outreach engine in the background
# Redirect output to PID 1's stdout/stderr so Cloud Run captures logs
echo "[STARTUP] Starting outreach engine (run.py) in background..."
(cd /app/prospect-outreach && python -u run.py) > /proc/1/fd/1 2>/proc/1/fd/2 &
OUTREACH_PID=$!
echo "[STARTUP] Outreach engine PID=$OUTREACH_PID"

# Start Streamlit in the foreground (Cloud Run health checks need this)
echo "[STARTUP] Starting Streamlit on port $PORT..."
exec streamlit run streamlit_app/app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
