FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY streamlit_app/ ./streamlit_app/
COPY .streamlit/ ./.streamlit/
COPY prospect-outreach/ ./prospect-outreach/

# Copy service account key for BigQuery access
COPY rcwl-development-0c013e9b5c2b.json ./rcwl-development-0c013e9b5c2b.json
ENV GCP_SERVICE_ACCOUNT_KEY=/app/rcwl-development-0c013e9b5c2b.json

# Expose Streamlit port
EXPOSE 8080

# Cloud Run sets PORT env var
ENV PORT=8080

# Run Streamlit
CMD streamlit run streamlit_app/app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
