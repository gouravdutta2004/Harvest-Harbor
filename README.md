<p align="center">
  <img src="frontend/public/logo.png" alt="Harvest Harbor Logo" width="260" />
</p>

<h1 align="center">Harvest Harbor (AI Crop Intelligence)</h1>

<p align="center">
  <strong>Interpretable Foliar Pathology Diagnostics, Temperature Calibration, U-Net Lesion Segmentation &amp; Cryptographic Evidence Ledger</strong><br />
  Enterprise-grade decision support platform empowering farmers, agronomists, and agricultural auditors.
</p>

<p align="center">
  <a href="https://github.com/gouravdutta2004/Harvest-Harbor"><img src="https://img.shields.io/badge/GitHub-Harvest--Harbor-10b981?style=for-the-badge&logo=github&logoColor=white" alt="GitHub Repository" /></a>
  <img src="https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.11-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="Backend" />
  <img src="https://img.shields.io/badge/Frontend-React%2018%20%7C%20Vite%20%7C%20Tailwind-61dafb?style=for-the-badge&logo=react&logoColor=black" alt="Frontend" />
  <img src="https://img.shields.io/badge/AI%20Models-EfficientNet--B0%20%2B%20U--Net-ff6f00?style=for-the-badge&logo=tensorflow&logoColor=white" alt="AI Models" />
  <img src="https://img.shields.io/badge/Tests-83%2F83%20Passing-brightgreen?style=for-the-badge&logo=checkmarx&logoColor=white" alt="Tests" />
  <img src="https://img.shields.io/badge/Ledger-SHA--256%20Evidence%20Chain-8b5cf6?style=for-the-badge&logo=blockchain&logoColor=white" alt="Security" />
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License" />
</p>

---

## 📌 Overview

**Harvest Harbor** is a production-grade, research-grounded artificial intelligence platform designed for precision crop pathology. By fusing convolutional feature extraction, post-hoc probability calibration, spatial lesion segmentation, visual attention attribution, and an immutable cryptographic audit ledger, the platform delivers verifiable, explainable, and tamper-evident agricultural diagnostics.

Unlike black-box classification scripts, Harvest Harbor integrates a **gated multi-tier diagnostic architecture** that cross-validates botanical crop family priors against disease candidates, generates pixel-level necrosis masks, exposes attention heatmaps via Grad-CAM, and preserves forensic audit records anchored to an append-only SHA-256 evidence chain.

---

## 🏗️ System Architecture & Inference Pipeline

The system processes field leaf photography through an end-to-end, multi-stage operational pipeline:

<p align="center">
  <img src="docs/figures/system_block_diagram.png" alt="Harvest Harbor System Architecture Block Diagram" width="100%" />
</p>
<p align="center">
  <em>Figure: End-to-End System Architecture Block Diagram. Vector SVG available at <a href="docs/figures/system_block_diagram.svg">docs/figures/system_block_diagram.svg</a>.</em>
</p>

### Pipeline Execution Flow:
1. **Specimen Ingestion & Pre-Flight Quality Guard:**
   - Validates MIME headers, magic bytes, and enforces a 15 MB file size limit.
   - Decompression-bomb defense rejects inputs exceeding 50 megapixels.
   - Dispatches tensors via dual-stream executor: $224 \times 224$ for classification backbones, $256 \times 256$ for U-Net segmentation.
2. **Tier-1 Binary Health Screening & Calibration:**
   - EfficientNet-B0 classifies foliage as **Healthy ($C_0$)** vs. **Diseased ($C_1$)**.
   - Applies post-hoc **Temperature Scaling** ($T = 0.05$) to mitigate neural overconfidence.
   - **Gating Decision:** If classified healthy ($\ge 60\%$), disease diagnosis is suppressed and a Good Agricultural Practices (GAP) certificate is issued. If diseased, the specimen advances to pathology tiers.
3. **Tier-2 Botanical Species Identification:**
   - Dedicated 14-class EfficientNet-B0 identifies the plant family (Apple, Corn, Grape, Potato, Tomato, etc.) with **100% Top-1 accuracy** on held-out test splits.
4. **Tier-3 Pathology Classification & Compatibility Gating:**
   - PlantWild-v2 115-class classifier generates candidate pathology logits.
   - **Crop-Aware Compatibility Filter:** Cross-references predicted crop species against pathology domains to eliminate cross-species false positives (e.g., rejecting Apple Scab if the leaf is Tomato).
5. **Tier-4 Spatial Lesion Segmentation & Severity Quantification:**
   - Deep U-Net network ($256 \times 256$ SavedModel) generates pixel masks distinguishing background, healthy blade, and necrotic lesions.
   - Quantitative Severity Engine computes: $\text{Severity} = \frac{\sum P_{\text{lesion}}}{\sum P_{\text{leaf}}} \times 100\%$, categorizing into 4 tiers: Healthy (0%), Early (<15%), Moderate (15–35%), Severe ($\ge 35\%$).
6. **Tier-5 Visual Explainability (Grad-CAM):**
   - Extracts gradients from the `top_activation` convolutional layer to produce high-resolution attention heatmaps overlaid on the original leaf image.
7. **Tier-6 Cryptographic Evidence Ledger (Blockchain):**
   - Every inference request generates a report ID (`CR-XXXXXXXXXXXX`) and an immutable block linked via SHA-256 hashes ($H_n = \text{SHA-256}(H_{n-1} \parallel \text{Report Data})$).
   - Concurrency file-locking guarantees zero ledger corruption or race conditions.
8. **Tier-7 Human-in-the-Loop Agronomist Review Queue:**
   - Automatically triages specimens flagged with high severity, low confidence, or diagnostic discrepancies into priority queues for expert resolution.

---

## 🔬 Empirical Research Evaluation

All metrics reflect evaluations on official held-out test sets using the production model weights packaged with Harvest Harbor:

| Subsystem | Neural Architecture | Metric | Empirical Value | Evaluation Dataset / Test Split |
|---|---|---|---|---|
| **Binary Health Screening** | EfficientNet-B0 | Accuracy | **100.00%** | PlantVillage Held-Out Test ($N=50$) |
| | | Sensitivity / Specificity | **100.00% / 100.00%** | Balanced Healthy vs. Diseased |
| **Dedicated Crop Classifier** | EfficientNet-B0 | Top-1 Accuracy | **100.00%** | Held-Out Test Split ($N=140$, 14 Crops) |
| | | Top-3 Accuracy | **100.00%** | 10 Samples Per Crop Family |
| **U-Net Lesion Segmentation** | U-Net ($256 \times 256$) | Mean IoU (Jaccard) | **44.30%** | PlantSeg Benchmark Test Set ($N=50$) |
| | | Mean Dice ($F_1$) | **55.52%** | Pixel-Level Necrotic Ground Truth |
| | | Pixel Precision / Recall | **61.33% / 65.22%** | Lesion Segmentation Mask |
| **Foliar Severity Tiering** | Area Ratio Formulation | Tier Classification Acc | **52.00%** | PlantSeg Ground Truth vs. Predicted Tiers |
| | | Mean Absolute Error (MAE) | **13.95%** | Absolute Foliar Area Deviation |
| **Probability Calibration** | Temperature Scaling | Uncalibrated ECE ($T=1.0$) | **2.30%** | Expected Calibration Error |
| | | Calibrated ECE ($T=0.05$) | **1.00%** | **56.5% Relative Error Reduction** |

*Complete empirical formulations, confusion matrices, and LaTeX tables are available in [docs/RESEARCH_EVALUATION.md](docs/RESEARCH_EVALUATION.md).*

---

## 📊 Publication Figures Index

All evaluation charts and confusion matrices are generated in publication-grade 300-DPI raster PNG and vector SVG:

| Figure | Description | File Links |
| :---: | :--- | :--- |
| **Figure 1** | 14×14 Dedicated Crop Classifier Confusion Matrix | [PNG](docs/figures/fig1_crop_confusion_matrix.png) |
| **Figure 2** | 4×4 Foliar Severity Tier Confusion Matrix | [PNG](docs/figures/fig2_severity_confusion_matrix.png) |
| **Figure 3** | 2×2 Binary Health Screening Confusion Matrix | [PNG](docs/figures/fig3_health_confusion_matrix.png) |
| **Figure 4** | U-Net Lesion Segmentation Benchmark Metrics | [PNG](docs/figures/fig4_segmentation_performance.png) |
| **Figure 5** | Expected Calibration Error (ECE) Temperature Scaling | [PNG](docs/figures/fig5_calibration_reliability_diagram.png) |
| **Figure 6** | Per-Class $F_1$-Scores across Evaluated Pathologies | [PNG](docs/figures/fig6_disease_per_class_f1.png) |
| **Figure 7** | System Architecture & Inference Flow Diagram | [PNG](docs/figures/fig7_system_architecture_pipeline.png) \| [SVG](docs/figures/fig7_system_architecture_pipeline.svg) |

---

## 🧠 AI Model Zoo & Cryptographic Fingerprints

To ensure strict scientific reproducibility and tamper prevention, every model artifact's SHA-256 hash is verified at application startup:

| Model Subsystem | Architecture | Artifact File Path | SHA-256 Cryptographic Hash |
| :--- | :--- | :--- | :--- |
| **Disease Model** | EfficientNet-B0 (115 Classes) | `backend/model/plantwild_v2_efficientnetb0.keras` | `411611a0977eaba38ae616635ecb8e7f6c1299cb0e9f89f585896786adb6802c` |
| **Crop Model** | EfficientNet-B0 (14 Species) | `backend/crop_model/crop_efficientnetb0.keras` | `b473ae77ca426e6910ec76d40c640732d30eb02c98cf3cee941b56b573a0d331` |
| **Health Model** | EfficientNet-B0 (Binary) | `backend/health_model/health_disease_efficientnetb0.keras` | `bb961155086400507012b3d5202c585ee54289bcbbffcbc3baa4abed585689f5` |
| **Segmentation Source** | Custom U-Net ($256 \times 256$) | `backend/segmentation_model/unet_plantseg.keras` | `11eaadaea1723edb86fca13bc4aade6a483f37e75b4d6658390cb63479221145` |
| **Segmentation Runtime** | TensorFlow SavedModel Dir | `backend/segmentation_model/unet_plantseg_savedmodel/` | `622ac75ee8c7c12e7701384946540e1654a7073c111521f7c2cbadb433b895c8` |

---

## 🛡️ Security & Zero-Trust Governance

Harvest Harbor is engineered for hardened enterprise deployments:

* **Fail-Closed Authentication:** Production mode rejects all unauthenticated API requests with HTTP 401 Unauthorized unless explicit API keys are configured via `HARVEST_HARBOR_API_KEYS`.
* **Timing-Attack Resistance:** API key comparisons use constant-time `hmac.compare_digest`.
* **Role-Based Access Control (RBAC):**
  * `farmer`: Scan leaves, view diagnostic reports, print GAP certificates.
  * `agronomist`: Review queue triage, expert diagnostic overrides, severity calibration.
  * `auditor`: Cryptographic evidence verification, ledger query, audit exports.
  * `admin`: System-wide access, log audits, worker thread configuration.
* **Path Traversal Protection:** Static asset delivery endpoints (`/uploads/*` and `/generated/*`) enforce absolute-path resolution and canonical prefix checks, blocking directory traversal attacks (`../`, `%2F`).
* **Zero Path Leakage:** Internal server file paths (`/Users/`, `/home/`, `/private/`) are sanitized from all external API responses.
* **Security Headers:** Enforces strict `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and `Permissions-Policy`.
* **Concurrency & Rate Limiting:** Sliding-window rate limiter (100 requests/minute per client IP) and async worker semaphore prevent Denial-of-Service and GPU memory exhaustion.

---

## 🚀 Quickstart & Installation

### Prerequisites
* **Python**: 3.11.x (managed via virtual environment)
* **Node.js**: 18.x or 20.x with `npm`

### 1. Clone Repository
```bash
git clone https://github.com/gouravdutta2004/Harvest-Harbor.git
cd Harvest-Harbor
```

### 2. Backend Setup
```bash
# Setup Python 3.11 virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# Start FastAPI server
cd backend
KERAS_HOME=./.keras ../.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```
*Backend API Swagger docs will be accessible at: `http://127.0.0.1:8000/docs`*

### 3. Frontend Setup
```bash
# In a new terminal window:
cd frontend

# Install dependencies and start Vite development server
npm install
npm run dev
```
*Frontend application will be accessible at: `http://localhost:5173`*

### 4. Build Production Bundle
```bash
cd frontend
npm run build
```

---

## 🧪 Testing & Quality Assurance

The codebase includes an exhaustive test suite covering unit contracts, security rules, regression scenarios, and end-to-end user journeys:

```bash
# Run all 83 backend regression tests
cd backend
PYTHONPATH=. ../.venv/bin/python -m unittest discover -s . -p "test*.py" -v
```

### Test Suite Summary:
* `test_prediction.py` (25 tests): Output shape, confidence bounds, and contract verification across all 4 ML models.
* `test_http_security.py` (12 tests): RBAC permissions, path traversal guard, unauthenticated rejection, and security headers.
* `test_regression.py` (4 tests): Multi-crop pipeline integration and review queue unique UUID generation.
* `test_security_and_science.py` (22 tests): Probability calibration, crop-disease gating, and reviewer identity auditing.
* `test_e2e_scenarios.py` (12 tests): All 12 core platform operational scenarios.
* `test_final_correctness.py` (7 tests): JSON path sanitization, error response contracts, and ledger integrity.
* `test_rejection.py` (1 test): Rejection behavior for incompatible crop-disease pairs.
* **Result: 83 / 83 Tests Passing (0 Failures, 0 Errors)**

---

## 📡 REST API Specifications

| Method | Endpoint | Role | Description |
| :---: | :--- | :---: | :--- |
| `GET` | `/health` | Public | System status, GPU availability, and model readiness. |
| `POST` | `/predict` | `farmer`+ | Upload leaf image for full multi-tier diagnostic analysis. |
| `GET` | `/uploads/{filename}` | `farmer`+ | Authenticated retrieval of uploaded leaf images. |
| `GET` | `/generated/{subpath}` | `farmer`+ | Authenticated download of Grad-CAM heatmaps and masks. |
| `GET` | `/traceability/chain` | `auditor`+ | Inspect the full SHA-256 tamper-evident evidence chain. |
| `GET` | `/traceability/verify` | `auditor`+ | Cryptographically verify ledger genesis and parent block hashes. |
| `GET` | `/traceability/report/{id}` | `farmer`+ | Reconstruct historical diagnostic report and audit trail. |
| `GET` | `/review-queue` | `agronomist`+ | Retrieve active human triage queue sorted by priority. |
| `POST` | `/review-queue/{id}/resolve`| `agronomist`+ | Submit agronomist resolution notes, decision override, and append block. |

---

## ⚠️ Scientific & Agronomic Disclaimers

1. **Decision Support Only:** Harvest Harbor is designed as an agricultural decision-support tool. It does not replace on-site physical inspection by certified extension pathologists or laboratory pathogen culture assays.
2. **Dataset Domain Specificity:** Performance benchmarks were evaluated on held-out splits of standardized research datasets (PlantVillage / PlantWild). Real-world lighting variations, specular reflections, camera blur, and non-foliar occlusions may affect confidence scores.
3. **Segmentation Halos:** Foliar lesions exhibiting chlorotic (yellowish) transition halos may yield boundary variances. Quantitative severity estimates should be corroborated through physical scouting prior to pesticide or fungicide application.
4. **Grad-CAM Attention:** Saliency maps highlight convolutional activations contributing to classification; they do not constitute microbiological proof of pathogen viability.

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
