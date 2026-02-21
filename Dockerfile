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

# Copy startup script
COPY start.sh ./start.sh
RUN chmod +x start.sh

# Expose Streamlit port
EXPOSE 8080

# Cloud Run sets PORT env var
ENV PORT=8080

# Run both Streamlit and outreach engine
CMD ["./start.sh"]
