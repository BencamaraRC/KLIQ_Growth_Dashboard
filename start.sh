#!/bin/bash
# Start the prospect outreach engine in the background
echo "[STARTUP] Starting outreach engine (run.py) in background..."
cd /app/prospect-outreach && python run.py &

# Start Streamlit in the foreground (Cloud Run health checks need this)
echo "[STARTUP] Starting Streamlit on port $PORT..."
exec streamlit run streamlit_app/app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
