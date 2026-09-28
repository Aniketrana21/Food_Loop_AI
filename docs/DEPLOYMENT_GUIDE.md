# FoodLoop AI — Enterprise Production Deployment Guide

This comprehensive guide details the complete production deployment architecture, step-by-step procedures, and operational runbooks for **FoodLoop AI**.

---

## Architecture Overview

```
                      +---------------------------------------+
                      |             Cloudflare / DNS          |
                      |  SSL/TLS (HTTPS) + DDoS Protection     |
                      +-------------------+-------------------+
                                          |
                   +----------------------+----------------------+
                   |                                             |
                   v                                             v
         https://foodloop.org                         https://api.foodloop.org
       +-----------------------+                    +---------------------------+
       |   Vercel Platform     |                    | Cloud Container / Server  |
       |  Next.js 14 Frontend  |                    | (Cloud Run / Render / ECS)|
       |  (Static / SSR / Edge)|                    |  FastAPI Backend Engine   |
       +-----------+-----------+                    +-------------+-------------+
                   |                                              |
                   | (Client Auth & Static CDN)                   | (SQLAlchemy 2.0 Pool)
                   v                                              v
       +------------------------------------------------------------------------+
       |                      Supabase Cloud Infrastructure                     |
       |  - PostgreSQL 16 (PostGIS 3.4 Spatial Extensions)                      |
       |  - PgBouncer Connection Pooler (Transaction / Session mode)           |
       |  - Supabase Storage (S3-compatible Object Storage for docs/images)     |
       |  - Supabase Auth (Row-Level Security / JWT)                            |
       +------------------------------------------------------------------------+
                                          |
                                          v
       +------------------------------------------------------------------------+
       |                      Third-Party Enterprise APIs                       |
       |  - Google Gemini 1.5 Pro / Flash (Surplus & RAG Engine)                |
       |  - Mapbox Directions & Optimization API (Vehicle Routing)              |
       |  - Sentry APM & Prometheus Observability Monitoring                    |
       +------------------------------------------------------------------------+
```

---

## 1. Database Setup (Supabase PostgreSQL & PostGIS)

### 1.1 Provisioning
1. Sign in to [Supabase Console](https://supabase.com/dashboard) and create a new project:
   - **Organization**: Your Enterprise Org
   - **Project Name**: `foodloop-production`
   - **Region**: Choose closest to target operations (e.g. `us-east-1` or `ap-northeast-1`)
   - **Database Password**: Generate a secure 32+ character passphrase and store in your password manager.

### 1.2 Enable Spatial Extensions & Initialize Schema
Execute the following commands in the Supabase SQL Editor:

```sql
-- 1. Enable PostGIS Spatial Extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2. Verify PostGIS installation
SELECT PostGIS_Full_Version();
```

3. Run the core schema migration:
   - Open and copy the contents of `database/schema.sql` into the Supabase SQL Editor and execute.
   - Verify that all tables, foreign keys, and indexes (`idx_listings_location`, `idx_organizations_location`, `idx_routes_geom`) are created.
4. Optional Seed Data (Staging only):
   - Run `database/seed.sql` to populate sample organizations, kitchens, and recipients for validation.

### 1.3 Connection Pooler Configuration
Supabase provides two connection strings:
- **Direct Connection** (Port `5432`): Use strictly for migrations and schema DDL.
- **Connection Pooler (PgBouncer)** (Port `6543` / `5432` with pooler hostname):
  - **Transaction Mode** (Port `6543`): Optimal for high-concurrency API serverless requests.
  - **Session Mode** (Port `5432` on pooler): Used by SQLAlchemy when prepared statements or session-level locks are required.
  - Set `DATABASE_URL` with SSL mode enabled:
    ```
    postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require
    ```

---

## 2. Environment Variables & Secret Hygiene

### 2.1 Critical Security Rules
- **NEVER** commit real secrets, API keys, or production database URLs to Git repositories.
- Use `.env.example` as a template.
- All secrets are injected through runtime environment variables or Cloud Secret Managers.

### 2.2 Production Variable Reference

| Variable | Environment | Scope | Description |
| :--- | :--- | :--- | :--- |
| `PROJECT_NAME` | Backend | Public | Application title (`FoodLoop AI`) |
| `ENVIRONMENT` | Backend | Server | `production` (enforces HTTPS redirect & secure cookies) |
| `API_V1_STR` | Backend | Public | API router prefix (`/api/v1`) |
| `SECRET_KEY` | Backend | Secret | 64-char hex key for JWT encryption (`openssl rand -hex 32`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Backend | Server | Token TTL (e.g. `1440` for 24 hours) |
| `DATABASE_URL` | Backend | Secret | PostgreSQL connection string with SSL |
| `SUPABASE_URL` | Both | Public | Supabase project API gateway URL |
| `SUPABASE_KEY` | Both | Public | Supabase anonymous public client key |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend | Secret | Admin bypass key for backend worker tasks |
| `LLM_PROVIDER` | Backend | Server | `gemini` (or `openai`, `anthropic`, `mock`) |
| `GEMINI_API_KEY` | Backend | Secret | Google AI Studio Gemini API Key |
| `MAPBOX_ACCESS_TOKEN` | Both | Server/Public| Mapbox API access token for spatial routing |
| `BACKEND_CORS_ORIGINS` | Backend | Server | JSON array: `["https://foodloop.org","https://app.foodloop.org"]` |
| `LOG_LEVEL` | Backend | Server | Logging threshold (`INFO` or `WARNING`) |
| `PROMETHEUS_METRICS_ENABLED`| Backend | Server | `true` (enables `/metrics` endpoint) |
| `NEXT_PUBLIC_API_URL` | Frontend | Public | Base backend API endpoint (`https://api.foodloop.org/api/v1`) |
| `NEXT_PUBLIC_SUPABASE_URL` | Frontend | Public | Client Supabase endpoint |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Frontend| Public | Client Supabase anon key |
| `NEXT_PUBLIC_MAPBOX_TOKEN`| Frontend | Public | Public Mapbox map rendering token |

---

## 3. Backend Deployment (FastAPI on Cloud Run / Render / AWS ECS)

### 3.1 Container Architecture
The backend uses a hardened, multi-stage Docker build:
- Base image: `python:3.11-slim`
- Runs as non-root user `appuser` (UID: 10001, GID: 10001)
- Bundles libpq5 and curl for health probes
- Includes automated health check: `HEALTHCHECK --interval=20s --timeout=5s CMD curl -f http://localhost:8000/health || exit 1`

### 3.2 Building and Pushing Container
```bash
# Set your container registry tag
export IMAGE_TAG="gcr.io/foodloop-prod/backend:v2.0.0"

# Build production container image
docker build -t $IMAGE_TAG -f Dockerfile .

# Authenticate to container registry
gcloud auth configure-docker # or: docker login

# Push to container registry
docker push $IMAGE_TAG
```

### 3.3 Deploying to Google Cloud Run
```bash
gcloud run deploy foodloop-backend \
  --image gcr.io/foodloop-prod/backend:v2.0.0 \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --min-instances 1 \
  --max-instances 10 \
  --cpu 1 \
  --memory 2Gi \
  --set-env-vars ENVIRONMENT=production,LOG_LEVEL=INFO,PROJECT_NAME="FoodLoop AI" \
  --set-secrets DATABASE_URL=FOODLOOP_DB_URL:latest,SECRET_KEY=FOODLOOP_JWT_SECRET:latest,GEMINI_API_KEY=GEMINI_KEY:latest
```

### 3.4 Deploying to Render.com
1. Create a **New Web Service** connected to your repository.
2. Set Environment to **Docker** and Dockerfile path to `Dockerfile`.
3. Set Instance Type: Standard (1 vCPU, 2GB RAM).
4. Under **Health Check Path**, enter: `/health`.
5. Under **Environment Variables**, paste all required backend secrets.

---

## 4. Frontend Deployment (Next.js on Vercel)

### 4.1 Vercel Integration
1. Push your repository to GitHub.
2. In [Vercel Dashboard](https://vercel.com), click **Add New Project** and select `FoodLoop_AI`.
3. Configure Project Settings:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Node.js Version**: `20.x`

### 4.2 Configure Environment Variables in Vercel
Add the following in Vercel **Settings → Environment Variables**:
- `NEXT_PUBLIC_API_URL` = `https://api.foodloop.org/api/v1`
- `NEXT_PUBLIC_SUPABASE_URL` = `https://[project-ref].supabase.co`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` = `sb_publishable_...`
- `NEXT_PUBLIC_MAPBOX_TOKEN` = `pk....`

### 4.3 Production Standalone Verification
The frontend is pre-configured with `next.config.mjs` using `output: 'standalone'` and full security headers:
- `Strict-Transport-Security` (HSTS)
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: origin-when-cross-origin`

---

## 5. AI Model Deployment & Provider Resilience

### 5.1 Provider-Agnostic LLM Engine
FoodLoop AI utilizes a multi-tiered fallback architecture:
1. **Primary Provider**: Google Gemini 1.5 Pro / Flash via `google-generativeai`.
2. **Secondary Provider**: OpenAI GPT-4o via OpenAI API client.
3. **Tertiary Provider**: Anthropic Claude 3.5 Sonnet.
4. **Offline / Fallback Mode**: Local rule-based heuristics and local mock engine.

### 5.2 Scikit-Learn / XGBoost Machine Learning Models
- Model artifacts are loaded into memory on container startup:
  - `ml/models/shelf_life_xgb.pkl` (Surplus expiration forecast)
  - `ml/models/waste_forecaster.pkl` (Kitchen production waste trend analysis)
  - `ml/models/dispatch_optimizer.pkl` (Fleet allocation matrix)
- If model files are absent, the system gracefully falls back to statistical baseline formulas without throwing 500 errors.

---

## 6. Storage Configuration (Supabase Storage)

### 6.1 Required Storage Buckets
Configure three dedicated S3-compatible buckets in Supabase:
1. `foodloop-documents`: Compliance certificates, inspection PDFs, food safety audits.
2. `foodloop-images`: Kitchen inventory photos, food verification scans.
3. `foodloop-avatars`: Organization profile photos and driver avatars.

### 6.2 Storage Access Policies (Row-Level Security)
```sql
-- Create buckets
INSERT INTO storage.buckets (id, name, public)
VALUES
  ('foodloop-documents', 'foodloop-documents', false),
  ('foodloop-images', 'foodloop-images', true),
  ('foodloop-avatars', 'foodloop-avatars', true)
ON CONFLICT (id) DO NOTHING;

-- Public Read for Food Images
CREATE POLICY "Public Read Food Images"
ON storage.objects FOR SELECT
USING (bucket_id = 'foodloop-images');

-- Authenticated Upload for Food Images
CREATE POLICY "Authenticated Upload Food Images"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'foodloop-images');

-- Strict Organization Tenant Isolation for Documents
CREATE POLICY "Tenant Isolated Document Access"
ON storage.objects FOR SELECT
TO authenticated
USING (
  bucket_id = 'foodloop-documents' AND
  (storage.foldername(name))[1] = auth.jwt() ->> 'org_id'
);
```

---

## 7. Domain Configuration & HTTPS / SSL

### 7.1 DNS Records Setup
Configure the following DNS records at your domain registrar (e.g., Cloudflare, Route53, Namecheap):

| Record Type | Host | Points To / Value | TTL | Proxy / SSL |
| :--- | :--- | :--- | :--- | :--- |
| `CNAME` | `foodloop.org` | `cname.vercel-dns.com` | Auto | Enabled |
| `CNAME` | `app` | `cname.vercel-dns.com` | Auto | Enabled |
| `CNAME` | `api` | `your-cloudrun-or-render.domain.com` | Auto | Enabled |

### 7.2 SSL / TLS Enforcement
- Cloudflare SSL/TLS encryption mode: **Full (Strict)**
- Minimum TLS Version: **TLS 1.2** (TLS 1.3 Recommended)
- HSTS (`Strict-Transport-Security`): Max age set to 2 years (`63072000` seconds) with subdomains and preload included.
- Backend redirects unencrypted HTTP traffic arriving from reverse proxies to HTTPS with HTTP `308 Permanent Redirect`.

---

## 8. Monitoring, Health Checks & Observability

### 8.1 Orchestrator Probes
The backend exposes dedicated health endpoints:

1. **Liveness Probe**: `GET /health` (also aliased at `GET /api/v1/health`)
   - Returns HTTP `200 OK`
   - Payload:
     ```json
     {
       "status": "healthy",
       "service": "foodloop-backend",
       "version": "2.0.0",
       "environment": "production",
       "uptime_seconds": 3600.5,
       "timestamp": "2026-09-28T15:00:00Z"
     }
     ```
2. **Readiness Probe**: `GET /ready` (also aliased at `GET /api/v1/ready`)
   - Actively checks PostgreSQL connection with `SELECT 1`.
   - Returns HTTP `200 OK` when healthy:
     ```json
     {
       "status": "ready",
       "database": "connected",
       "dialect": "postgresql",
       "checks": { "database": "pass", "filesystem": "pass" }
     }
     ```
   - Returns HTTP `503 Service Unavailable` if database is down, automatically signaling load balancers to halt traffic routing.

### 8.2 Prometheus Metrics
- Endpoint: `GET /metrics`
- Scraped by Prometheus / Datadog / Grafana Agent every 15 seconds.
- Exports application uptime and service health gauges.

### 8.3 Centralized Logging & Error Tracking
- Every request is stamped with a unique `X-Request-ID` via `RequestIDMiddleware`.
- Structured JSON log records are emitted to `stdout` for ingestion into CloudWatch, Google Cloud Logging, or Datadog.
- Optional Sentry APM integration via `SENTRY_DSN` captures uncaught runtime exceptions with stack traces.

---

## 9. Backup & Disaster Recovery Strategy

### 9.1 Database Backup Schedule
1. **Automated Supabase Backups**:
   - Daily automated logical and physical snapshots retained for 30 days.
   - Point-In-Time Recovery (PITR) enabled with 7-day granular log replay.
2. **Offsite Automated Nightly Dump (Cron)**:
   ```bash
   #!/bin/bash
   # Run via secure CI/CD or cron job
   TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
   BACKUP_FILE="/backups/foodloop_db_${TIMESTAMP}.dump"
   pg_dump -Fc --no-owner --no-privileges -d "$DATABASE_URL" > "$BACKUP_FILE"
   aws s3 cp "$BACKUP_FILE" s3://foodloop-offsite-backups/daily/
   rm -f "$BACKUP_FILE"
   ```

### 9.2 Recovery Time Objective (RTO) & Recovery Point Objective (RPO)
- **RTO (Target Restoration Time)**: < 15 minutes for container reboot / failover; < 1 hour for full database restore from snapshot.
- **RPO (Maximum Data Loss)**: < 5 minutes with Supabase WAL archiving / PITR.

---

## 10. Rollback Strategy & Safe Deployments

### 10.1 Zero-Downtime Deployment
Deployments follow an immutable container paradigm:
1. Build new version tagged with git SHA (e.g., `:sha-8fa19bc`).
2. Cloud Run / Render spins up new container instances.
3. Traffic is only routed after `/ready` passes health checks on the new revision.

### 10.2 Instant Rollback Runbooks

#### Frontend Rollback (Vercel)
- Navigate to **Vercel Dashboard → Deployments**.
- Locate the last known good deployment.
- Click **Instant Rollback**. Vercel redirects 100% of edge CDN traffic to the prior build within 5 seconds without rebuilding.

#### Backend Rollback (Cloud Run)
```bash
# List recent revisions
gcloud run revisions list --service foodloop-backend --region us-central1

# Route 100% traffic immediately back to previous revision
gcloud run services update-traffic foodloop-backend \
  --region us-central1 \
  --to-revisions foodloop-backend-00042-xyz=100
```

#### Database Schema Rollback
- Database migrations must strictly follow the **Expand and Contract pattern**:
  1. **Phase 1 (Expand)**: Add new nullable columns or tables; deploy application supporting both old and new schema.
  2. **Phase 2 (Migrate)**: Migrate data in background.
  3. **Phase 3 (Contract)**: Drop deprecated columns after verifying all clients run updated code.
- Always verify that schema changes do not execute destructive `DROP TABLE` or `DROP COLUMN` commands during peak operational hours.
