# Harvest Harbor — Deployment & Operations Guide

> **Version:** 1.1.0 — Updated 2026-10-01  
> **Status:** Production-Ready / Demo-Ready  
> **Test Suite:** 78/78 tests passing  
> **Build:** `npm run build` → 0 errors, 1.59s

---

## 1. System Requirements & Environment

### Hardware Recommendations
- **CPU**: 4+ Cores (x86_64 or Apple Silicon ARM64)
- **RAM**: Minimum 8 GB (16 GB recommended for concurrent multi-model inference)
- **Disk**: 10 GB free space for models, datasets, and generated visualizations

### Software Dependencies
- **Backend**: Python 3.10+ (Tested on Python 3.11 with TensorFlow 2.15.0)
- **Frontend**: Node.js 18+ (Tested on Node 20.x, Vite 5.4)

---

## 2. Environment Variables & Security Configuration

Configure the environment using `.env` or system environment variables:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `development` | Setting to `production` enforces strict authentication and fails closed if API keys are missing. |
| `HARVEST_HARBOR_API_KEYS` | *(Dev default keys)* | Comma-delimited list or JSON mapping of authorized API keys (`key1:role1,key2:role2`). |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000` | Whitelist of authorized web frontend origins for CORS. |
| `MAX_FILE_SIZE_BYTES` | `15728640` (15 MB) | Upload file size cap in bytes. |
| `MAX_DECODED_PIXELS` | `50000000` (50 MP) | Maximum allowable decompressed image pixel count. |
| `MAX_GENERATED_FILE_AGE_HOURS` | `24` | Retention policy in hours for generated heatmaps and segmentation overlays. |

### Frontend Environment Variables (`.env.development` / `.env.production`)

| Variable | Description |
| :--- | :--- |
| `VITE_API_BASE_URL` | Base URL of the FastAPI backend (default: `http://127.0.0.1:8000`). |
| `VITE_DEV_FARMER_KEY` | Dev-only API key for the Farmer role persona. |
| `VITE_DEV_AGRONOMIST_KEY` | Dev-only API key for the Agronomist role persona. |
| `VITE_DEV_AUDITOR_KEY` | Dev-only API key for the Auditor role persona. |
| `VITE_DEV_ADMIN_KEY` | Dev-only API key for the Admin role persona. |

> **Security Note:** Dev keys are read from `.env.development` only and are completely absent from production builds (`isProd` guard in `api.js`).

---

## 3. Local Development Quickstart

```bash
# 1. Clone / unzip the project
cd crop-disease-ai

# 2. Create and activate Python virtualenv
python3.11 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt

# 3. Start the FastAPI backend
cd backend
PYTHONPATH=. KERAS_HOME=.keras uvicorn app:app --host 127.0.0.1 --port 8000

# 4. In a second terminal — install frontend deps and start Vite
cd frontend
npm install
npm run dev -- --port 5173

# Open http://localhost:5173 in a browser
```

---

## 4. Production Deployment Options

### Option A: Systemd Service Architecture (Linux Host)

#### Backend Service (`/etc/systemd/system/harvest-backend.service`)
```ini
[Unit]
Description=Harvest Harbor FastAPI Backend
After=network.target

[Service]
User=harvest
WorkingDirectory=/var/www/crop-disease-ai/backend
Environment="PATH=/var/www/crop-disease-ai/backend/.venv/bin"
Environment="PYTHONPATH=/var/www/crop-disease-ai/backend"
Environment="ENVIRONMENT=production"
ExecStart=/var/www/crop-disease-ai/backend/.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Frontend Nginx Reverse Proxy (`/etc/nginx/sites-available/harvest-harbor`)
```nginx
server {
    listen 80;
    server_name harvest.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name harvest.example.com;

    ssl_certificate /etc/letsencrypt/live/harvest.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/harvest.example.com/privkey.pem;

    # Static Frontend SPA
    root /var/www/crop-disease-ai/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API Proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Protected Binary Assets (served directly by FastAPI with auth)
    location /uploads/ {
        proxy_pass http://127.0.0.1:8000/uploads/;
        proxy_set_header Host $host;
    }

    location /generated/ {
        proxy_pass http://127.0.0.1:8000/generated/;
        proxy_set_header Host $host;
    }
}
```

---

## 5. Frontend Build & Deployment

```bash
cd frontend
npm ci           # clean install from package-lock.json
npm run build    # outputs to frontend/dist/
```

The production build outputs to `frontend/dist/`. Serve it with any static file server or Nginx (see above).

> **Important:** `frontend/node_modules/` and `frontend/dist/` are **excluded** from the release ZIP. Run `npm ci && npm run build` on the deployment host.

---

## 6. Key Backend JSON Field Reference

These are the **actual field names** returned by the backend. Frontend components must read these exact keys:

| Path | Type | Description |
| :--- | :--- | :--- |
| `response.severity.severity` | `string` | Severity label: `"Healthy"`, `"Early"`, `"Moderate"`, or `"Severe"` |
| `response.severity.affected_area_percent` | `float` | Estimated % of leaf area affected |
| `response.severity.thresholds` | `object` | Project-defined boundaries (not independently validated) |
| `response.human_review.resolution_status` | `string` | Resolution decision: `"confirmed"`, `"rejected"`, `"needs_more_evidence"` |
| `response.human_review.required` | `bool` | Whether the report requires human review |
| `evidence_data.severity.severity` | `string` | Severity stored in the evidence chain block |
| `review_item.review_id` | `string` | Globally unique review ID (format: `REV-{12-HEX}`) — use as React key |
| `review_item.decision` | `string` | Resolution after resolve: `"confirmed"` / `"rejected"` / `"needs_more_evidence"` |
| `review_item.status` | `string` | `"pending"` or `"resolved"` |
| `image.url` | `string` | Backend-relative path (e.g. `/uploads/CR-XXXX_leaf.jpg`) — fetch via `AuthenticatedImage` |

> **Note:** The traceability chain's `evidenceData` does **not** have a top-level `image_url` field. The image URL is stored in `evidenceData.report_snapshot.image.url`.

---

## 7. Report Asset Lifecycle

Images are served via authenticated HTTP from `/uploads/` and `/generated/` backend endpoints. The `AuthenticatedImage` component and `useAuthenticatedImage` hook:

1. Receive a **backend-relative path** (e.g. `/uploads/CR-XXXX_leaf.jpg`)
2. Perform an authenticated `fetch()` with the current session's Bearer token
3. Convert the blob response to an `objectURL`
4. **Revoke the objectURL on component unmount** to prevent memory leaks

> **Critical:** Never pass a `blob:` URL to the Report page as `originalImage`. Blobs are revoked when their originating component unmounts. Always pass the backend-relative path (`image.url`) which is stable across page navigation and refreshes.

---

## 8. Maintenance & Operations

### Evidence Chain Backups
The local evidence chain (`backend/traceability/evidence_chain.json`) and review queue (`backend/traceability/review_queue.json`) use transactional file locking. To create hot backups:
```bash
# Atomic snapshot
cp backend/traceability/evidence_chain.json /backups/evidence_chain_$(date +%Y%m%d_%H%M%S).json
cp backend/traceability/review_queue.json /backups/review_queue_$(date +%Y%m%d_%H%M%S).json
```

### Automated Asset Cleanup
Temporary uploads and generated heatmaps should be purged periodically via the administrative cleanup endpoint:
```bash
curl -X POST http://127.0.0.1:8000/admin/cleanup \
     -H "Authorization: Bearer <ADMIN_API_KEY>" \
     -H "Content-Type: application/json" \
     -d '{"max_age_hours": 48}'
```
Or scheduled via cron:
```cron
0 2 * * * curl -s -X POST http://127.0.0.1:8000/admin/cleanup -H "Authorization: Bearer dev-admin-key" > /dev/null
```

### Running the Full Test Suite
```bash
# 78 backend tests (model loading, inference, severity, traceability, RBAC, security)
cd crop-disease-ai
backend/.venv/bin/python -m unittest discover -s backend -p "test_*.py"
# Expected: Ran 78 tests in ~42s — OK

# Frontend build verification
cd frontend && npm run build
# Expected: ✓ built in ~1.6s — 0 errors
```

---

## 9. Security Checklist

- [ ] Set `ENVIRONMENT=production` in all production deployments
- [ ] Rotate all API keys from dev defaults before go-live (`HARVEST_HARBOR_API_KEYS`)
- [ ] Configure `CORS_ORIGINS` to include only your production domain
- [ ] Enable HTTPS (TLS 1.2+) via Nginx/Caddy reverse proxy
- [ ] Ensure `/uploads/` and `/generated/` assets require authentication (FastAPI enforces this)
- [ ] Verify the SHA-256 evidence chain is intact: `GET /traceability/verify`
- [ ] Review `backend/traceability/review_queue.json` for any unresolved high-priority items
- [ ] Confirm `frontend/dist/` does NOT contain `.env.development` secrets
