# ==============================================================================
# GatherFlow AI — Google Cloud Run Automated Deployment Script (PowerShell)
# ==============================================================================
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  GatherFlow AI — Deploying to Google Cloud Run" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify gcloud CLI
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Error "Google Cloud SDK (gcloud) is not installed or not in PATH. Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
}

# 2. Check GCP Project
$projectId = (gcloud config get-value project 2>$null).Trim()
if ([string]::IsNullOrWhiteSpace($projectId) -or $projectId -eq "(unset)") {
    $projectId = Read-Host "Enter GCP Project ID"
    gcloud config set project $projectId
}
Write-Host "Deploying to GCP Project: $projectId" -ForegroundColor Green

# 3. Read GEMINI_API_KEY
$geminiKey = $env:GEMINI_API_KEY
if ([string]::IsNullOrWhiteSpace($geminiKey) -and (Test-Path .env)) {
    Get-Content .env | ForEach-Object {
        if ($_ -match "^GEMINI_API_KEY=(.*)$") {
            $geminiKey = $matches[1].Trim().Trim('"').Trim("'")
        }
    }
}
if ([string]::IsNullOrWhiteSpace($geminiKey)) {
    $geminiKey = Read-Host "Enter your Google Gemini API Key" -AsSecureString
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($geminiKey)
    $geminiKey = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
}

$region = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$serviceName = "gatherflow-ai"

# 4. Enable required GCP services
Write-Host "Enabling Cloud Run and Cloud Build APIs..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project=$projectId

# 5. Build and Deploy
Write-Host "Deploying container to Google Cloud Run (Region: $region)..." -ForegroundColor Yellow
gcloud run deploy $serviceName `
    --source . `
    --project $projectId `
    --region $region `
    --platform managed `
    --allow-unauthenticated `
    --min-instances 0 `
    --max-instances 5 `
    --memory 1Gi `
    --cpu 1 `
    --timeout 300s `
    --set-env-vars "ENVIRONMENT=production,GEMINI_MODEL=gemini-3.8-flash,EVALUATOR_PASSCODE=gatherflow-evaluator,GEMINI_API_KEY=$geminiKey,SESSION_SECRET_KEY=prod-secret-session-key-gatherflow-2026"

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Deployment Complete!" -ForegroundColor Green
$serviceUrl = (gcloud run services describe $serviceName --platform managed --region $region --format "value(status.url)" --project=$projectId).Trim()
Write-Host "  Live URL: $serviceUrl" -ForegroundColor Cyan
Write-Host "  Evaluator Passcode: gatherflow-evaluator" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green

