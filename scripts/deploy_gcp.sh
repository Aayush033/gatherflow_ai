#!/usr/bin/env bash
# ==============================================================================
# GatherFlow AI — Google Cloud Run Automated Deployment Script
# ==============================================================================
set -euo pipefail

echo "=========================================================="
echo "  GatherFlow AI — Deploying to Google Cloud Run"
echo "=========================================================="

# 1. Verify gcloud CLI
if ! command -v gcloud &> /dev/null; then
    echo "Error: Google Cloud SDK (gcloud) is not installed."
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# 2. Check GCP Project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
    echo "Please set your GCP project ID:"
    read -r -p "Enter GCP Project ID: " PROJECT_ID
    gcloud config set project "$PROJECT_ID"
fi
echo "Deploying to GCP Project: $PROJECT_ID"

# 3. Read GEMINI_API_KEY
if [ -z "${GEMINI_API_KEY:-}" ]; then
    if [ -f .env ]; then
        GEMINI_API_KEY=$(grep '^GEMINI_API_KEY=' .env | cut -d '=' -f2- | tr -d '"' | tr -d "'" || true)
    fi
fi

if [ -z "${GEMINI_API_KEY:-}" ]; then
    echo "GEMINI_API_KEY not found in environment or .env."
    read -r -s -p "Enter your Google Gemini API Key: " GEMINI_API_KEY
    echo ""
fi

REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="gatherflow-ai"

# 4. Enable required services
echo "Enabling Cloud Run and Cloud Build APIs..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project="$PROJECT_ID"

# 5. Build & Deploy using Cloud Run source deploy
echo "Deploying container to Google Cloud Run (Region: $REGION)..."
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --min-instances 0 \
    --max-instances 5 \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300s \
    --set-env-vars "ENVIRONMENT=production,GEMINI_MODEL=gemini-3.8-flash,EVALUATOR_PASSCODE=gatherflow-evaluator,GEMINI_API_KEY=$GEMINI_API_KEY,SESSION_SECRET_KEY=$(openssl rand -hex 16 2>/dev/null || echo 'prod-secret-session-key-gatherflow-2026')"

echo ""
echo "=========================================================="
echo "  Deployment Complete!"
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --platform managed --region "$REGION" --format 'value(status.url)' --project="$PROJECT_ID")
echo "  Live URL: $SERVICE_URL"
echo "  Evaluator Passcode: gatherflow-evaluator"
echo "=========================================================="

