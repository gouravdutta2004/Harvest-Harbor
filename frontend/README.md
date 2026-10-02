# HARVEST HARBOR — Frontend

Production AI Crop Disease Detection, Explainability (Grad-CAM), U-Net Segmentation, and Tamper-Evident SHA-256 Evidence Chain Web Application.

---

## 1. Overview & Architecture

Harvest Harbor frontend is a React 18 + Vite SaaS web platform designed for agricultural researchers, farmers, and agronomists. It connects directly to the existing Python FastAPI backend running at `http://127.0.0.1:8000`.

### Key Features
- **Crop Health Screening**: Binary screening (Healthy vs. Diseased) using EfficientNet-B0.
- **Disease Categorization**: Top-3 softmax probability distribution over 115 PlantWild disease categories.
- **Explainable AI (Grad-CAM)**: High-resolution activation heatmaps and overlays directly from convolutional layers (`top_activation`).
- **U-Net Lesion Segmentation**: segmentation-based estimation of visible affected regions and estimated affected-area percentage.
- **Severity Estimation**: Quantitative surface coverage categorization into `Healthy` (0%), `Early` (<15%), `Moderate` (15–35%), and `Severe` (≥35%) tiers with agronomic guidance.
- **Agronomic Knowledge Base**: Symptoms, causes, environmental triggers, immediate actions, and prevention guidelines.
- **Tamper-Evident SHA-256 Evidence Chain**: Cryptographic verification of image SHA-256 hashes, canonical report JSON digests, and chain linkages (`CR-...`).
- **Dark Mode**: High-contrast, clean theme with persistent localStorage preferences.
- **Responsive**: Professional desktop dashboard layout transforming into mobile drawer navigation on smaller screens.

---

## 2. Directory Structure

```text
frontend/
├── src/
│   ├── components/
│   │   ├── Sidebar.jsx              # Navigation and live backend status indicator
│   │   ├── Topbar.jsx               # Theme toggle, breadcrumbs, quick actions
│   │   ├── StatCard.jsx             # Reusable metric card with semantic badges
│   │   ├── UploadDropzone.jsx       # Drag & drop upload area with preview & format checks
│   │   ├── PredictionCard.jsx       # Prominent result banner & binary health bars
│   │   ├── ConfidenceBar.jsx        # Animated color-coded horizontal probability bars
│   │   ├── DiseaseRanking.jsx       # Ranked Top-3 diseases with class indices & scores
│   │   ├── GradCAMViewer.jsx        # Visual explainability with tabs, zoom, & side-by-side
│   │   ├── SegmentationViewer.jsx   # 4-panel composite view, donut chart, pixel metrics
│   │   ├── SeverityCard.jsx         # Severity stepper, stage descriptions, agronomic advice
│   │   ├── DiseaseInfo.jsx          # Tabbed agronomic symptoms, causes, & prevention
│   │   ├── TraceabilityCard.jsx     # Report ID, timestamp, image SHA-256, model versions
│   │   ├── BlockchainStatus.jsx     # Visual evidence chain timeline & cryptographic check
│   │   ├── HashDisplay.jsx          # 1-click copyable hash & ID component
│   │   ├── ReportCard.jsx           # AI-Assisted Assessment Report
│   │   └── LoadingState.jsx         # Pipeline progress stepper during inference
│   │
│   ├── pages/
│   │   ├── Dashboard.jsx            # Platform statistics, model statuses, recent records
│   │   ├── Analyze.jsx              # Core crop analysis workspace
│   │   ├── Report.jsx               # AI-assisted assessment report viewer & lookup by ID
│   │   ├── Traceability.jsx         # Evidence Chain Explorer & full chain verification
│   │   └── About.jsx                # System methodology, models, datasets & disclaimers
│   │
│   ├── services/
│   │   └── api.js                   # Centralized FastAPI client with asset URL resolver
│   │
│   ├── hooks/
│   │   ├── usePrediction.js         # Multi-stage prediction lifecycle management
│   │   └── useBackendStatus.js      # Live polling of /health & / root status
│   │
│   ├── utils/
│   │   └── formatters.js            # Numbers, percentages, dates, & semantic themes
│   │
│   ├── App.jsx                      # Root router, theme provider, and layout
│   ├── main.jsx                     # Vite React entrypoint
│   └── index.css                    # Tailwind CSS directives and custom styling
│
├── index.html                       # HTML template with typography preconnects
├── vite.config.js                   # Vite configuration
├── tailwind.config.js               # AgTech palette & dark mode configuration
├── postcss.config.js                # PostCSS configuration
├── package.json                     # Dependencies and scripts
└── .env                             # Environment configuration (VITE_API_BASE_URL)
```

---

## 3. Installation & Setup

From the `frontend/` directory:

```bash
# 1. Install dependencies
npm install

# 2. Start the development server
npm run dev
```

The frontend will run at:
- `http://localhost:5173`

---

## 4. Connecting to the Backend

By default, the frontend connects to:
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

To run the complete platform:
1. **Start the FastAPI backend** (from the repository root):
   ```bash
   .venv/bin/python backend/app.py
   # or: cd backend && uvicorn app:app --reload --port 8000
   ```
2. **Start the Vite frontend** (from `frontend/`):
   ```bash
   npm run dev
   ```

---

## 5. Backend API Endpoints Utilized

| Endpoint | Method | Component / Service | Description |
| :--- | :--- | :--- | :--- |
| `/health` | `GET` | `useBackendStatus` | Monitors operational status of 4 neural models & knowledge base |
| `/` | `GET` | `useBackendStatus` | Verifies system version and active routes |
| `/predict` | `POST` | `UploadDropzone`, `Analyze` | Multi-branch inference (Health, Disease, Grad-CAM, Segmentation, Severity, Traceability) |
| `/traceability/status` | `GET` | `Dashboard`, `Traceability` | Summary stats of the evidence chain |
| `/traceability/verify` | `GET` | `Traceability` | Validates hash integrity across all records in the evidence chain |
| `/traceability/chain` | `GET` | `Dashboard`, `Traceability`, `Report` | Fetches complete list of hash-linked evidence records |
| `/traceability/report/{report_id}` | `GET` | `Report`, `Traceability` | Retrieves recorded assessment record for a specific Report ID |
| `/generated/*` | `GET` | `GradCAMViewer`, `SegmentationViewer` | Static asset serving for heatmaps, masks, and composite images |
