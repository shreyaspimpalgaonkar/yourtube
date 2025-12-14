# YourTube.dev - Cloud Run Deployment

A simple landing page deployed on Google Cloud Run for yourtube.dev.

## Prerequisites

1. [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install)
2. A GCP project with billing enabled
3. Domain `yourtube.dev` ownership verified in Google Search Console

## Quick Deploy

### 1. Set your GCP Project ID

```bash
export GCP_PROJECT_ID="your-actual-project-id"
```

### 2. Deploy to Cloud Run

```bash
cd yourtube-cloudrun
chmod +x deploy.sh
./deploy.sh
```

Or manually:

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Deploy from source
gcloud run deploy yourtube-dev \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated
```

## Connecting Your Domain (yourtube.dev)

### Step 1: Verify Domain Ownership

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Add `yourtube.dev` as a property
3. Verify ownership via DNS TXT record

### Step 2: Map Domain in Cloud Run

```bash
gcloud run domain-mappings create \
    --service yourtube-dev \
    --domain yourtube.dev \
    --region us-central1
```

### Step 3: Configure DNS Records

After running the domain mapping command, you'll see DNS records to add.

Go to your domain registrar and add these DNS records:

| Type  | Name | Value |
|-------|------|-------|
| A     | @    | (IP from gcloud output) |
| AAAA  | @    | (IPv6 from gcloud output) |
| CNAME | www  | ghs.googlehosted.com. |

### Step 4: Wait for SSL

Google will automatically provision an SSL certificate. This can take up to 24 hours.

Check status:
```bash
gcloud run domain-mappings describe --domain yourtube.dev --region us-central1
```

## Local Development

```bash
pip install -r requirements.txt
python main.py
```

Visit http://localhost:8080

## Files

- `main.py` - Flask application with landing page
- `Dockerfile` - Container configuration
- `requirements.txt` - Python dependencies
- `deploy.sh` - Deployment automation script

## Useful Commands

```bash
# View service details
gcloud run services describe yourtube-dev --region us-central1

# View logs
gcloud run services logs read yourtube-dev --region us-central1

# Update the service
gcloud run deploy yourtube-dev --source . --region us-central1

# Delete the service
gcloud run services delete yourtube-dev --region us-central1
```

