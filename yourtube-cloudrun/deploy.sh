#!/bin/bash

# YourTube.dev Cloud Run Deployment Script
# =========================================

set -e

# Configuration - UPDATE THESE
PROJECT_ID="${GCP_PROJECT_ID:-your-gcp-project-id}"
REGION="us-central1"
SERVICE_NAME="yourtube-dev"

echo "🚀 Deploying YourTube.dev to Cloud Run..."
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Service: $SERVICE_NAME"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Authenticate and set project
echo "🔐 Setting GCP project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📦 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Deploy to Cloud Run (builds and deploys in one step)
echo "🏗️  Building and deploying..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "📋 Next steps to connect yourtube.dev:"
echo "   1. Run: gcloud run domain-mappings create --service $SERVICE_NAME --domain yourtube.dev --region $REGION"
echo "   2. Add DNS records as shown in the output"
echo "   3. Wait for SSL certificate provisioning (can take up to 24 hours)"

