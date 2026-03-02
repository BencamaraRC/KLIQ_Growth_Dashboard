#!/bin/bash
# Deploy the Dash app to Cloud Run
# Usage: ./deploy-dash.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=== Deploying KLIQ Dash Dashboard to Cloud Run ==="

# Swap Dockerfile temporarily
if [ -f Dockerfile ]; then
    mv Dockerfile Dockerfile.streamlit.bak
fi
mv Dockerfile.dash Dockerfile

# Deploy
/Users/bencamara/google-cloud-sdk/bin/gcloud run deploy kliq-dash-dashboard \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --timeout 300 \
  --project rcwl-development

# Restore Dockerfiles
mv Dockerfile Dockerfile.dash
if [ -f Dockerfile.streamlit.bak ]; then
    mv Dockerfile.streamlit.bak Dockerfile
fi

echo "=== Deployment complete ==="
