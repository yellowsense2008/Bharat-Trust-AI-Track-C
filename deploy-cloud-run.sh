#!/bin/bash
# deploy-cloud-run.sh
# Deployment script for Google Cloud Run

set -e

echo "🚀 Deploying Bharat Trust AI - Track C to Google Cloud Run"
echo "============================================================"

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-asia-south1}"
SERVICE_NAME="rbi-track-c-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Check if required environment variables are set
if [ -z "$GROQ_API_KEY" ]; then
    echo "❌ Error: GROQ_API_KEY environment variable is not set"
    exit 1
fi

if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  Warning: SECRET_KEY not set, generating one"
    SECRET_KEY="changeme-in-production-$(date +%s)"
fi

echo ""
echo "📋 Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Service: $SERVICE_NAME"
echo "   Image: $IMAGE_NAME"
echo ""

# Set GCP project
echo "🔧 Setting GCP project..."
gcloud config set project $PROJECT_ID

# Build container image
echo ""
echo "🏗️  Building container image..."
gcloud builds submit --tag $IMAGE_NAME

# Deploy to Cloud Run
echo ""
echo "🚢 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --add-cloudsql-instances build-for-bharat-yellowsense:asia-south1:grievance-db \
  --set-env-vars "GROQ_API_KEY=${GROQ_API_KEY}" \
  --set-env-vars "SECRET_KEY=${SECRET_KEY}" \
  --set-env-vars "DATABASE_URL=postgresql+psycopg2://grievance_user:GrievanceDB%402026@/grievance_db?host=/cloudsql/build-for-bharat-yellowsense:asia-south1:grievance-db" \
  --set-env-vars "ALGORITHM=HS256" \
  --set-env-vars "ACCESS_TOKEN_EXPIRE_MINUTES=1440"

# Get service URL
echo ""
echo "✅ Deployment complete!"
echo ""
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)')

echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "📝 Test endpoints:"
echo "   Health: $SERVICE_URL/health"
echo "   API Docs: $SERVICE_URL/docs"
echo ""
echo "🧪 Quick test:"
echo "   curl $SERVICE_URL/health"
echo ""
