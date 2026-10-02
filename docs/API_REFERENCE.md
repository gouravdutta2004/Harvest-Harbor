# Harvest Harbor — REST API Reference & Integration Guide

Base URL: `http://localhost:8000` (Development) / Configured Domain (Production)

---

## 1. Authentication & Security Headers

### Authentication Mechanisms
1. **Bearer Token**: `Authorization: Bearer <API_KEY>`
2. **Custom Header**: `X-API-Key: <API_KEY>`
3. **Role Specification**: `X-User-Role: <role>` (e.g., `farmer`, `agronomist`, `auditor`, `admin`)
4. **Inspector Identifier**: `X-Inspector-ID: <id>` (Audit tracking label)

### Role-Based Access Control (RBAC)
| Role | Permitted Actions |
| :--- | :--- |
| `farmer` | `scan`, `view_reports`, `print_reports` |
| `agronomist` | `scan`, `view_reports`, `verify_blockchain`, `calibrate_severity`, `export_protocols`, `review_reports`, `print_reports` |
| `auditor` | `view_reports`, `verify_blockchain`, `review_reports` |
| `admin` | `all` (including `/admin/cleanup`) |

### Security Headers Returned
- `Content-Security-Policy`: `default-src 'self'; frame-ancestors 'none'; ...`
- `Permissions-Policy`: `geolocation=(), camera=(), microphone=()`
- `X-Content-Type-Options`: `nosniff`
- `X-Frame-Options`: `DENY`
- `Strict-Transport-Security`: `max-age=31536000; includeSubDomains` (enabled when HTTPS / reverse-proxy header detected)

---

## 2. Core Diagnostics Endpoints

### `POST /predict`
Submit foliage image for comprehensive AI assessment, segmentation, explainability, and evidence chain stamping.

- **Content-Type**: `multipart/form-data`
- **Authentication**: Required (`scan` permission)
- **Parameters**:
  - `file`: Image file (`.jpg`, `.jpeg`, `.png`, `.webp`). Maximum 10 MB. Max decoded pixels: 50,000,000.
- **Response `200 OK`**:
```json
{
  "success": true,
  "report_id": "CR-B2C6154EE2D8",
  "timestamp": "2026-10-01T12:27:38.852Z",
  "image": {
    "filename": "diseased_leaf.jpg",
    "url": "/uploads/CR-B2C6154EE2D8_diseased_leaf.jpg",
    "sha256": "8315e1544638dc2664238c8a19bc9d4ce5b9f275755d943d36404c572115a70d",
    "width": 400,
    "height": 400,
    "format": "RGB"
  },
  "health_prediction": {
    "prediction": "diseased",
    "confidence": 100.0,
    "healthy_probability": 0.0,
    "diseased_probability": 100.0,
    "calibration": {
      "status": "temperature_scaled",
      "temperature": 0.05
    }
  },
  "crop_prediction": {
    "prediction": "Potato",
    "confidence": 100.0,
    "uncertain": false,
    "top_3": [
      { "rank": 1, "class": "Potato", "confidence": 100.0 }
    ]
  },
  "disease_analysis": {
    "prediction": "potato early blight",
    "confidence": 98.4,
    "validation": {
      "status": "valid",
      "reason": "Pathogen is botanically compatible with Potato."
    }
  },
  "explainability": {
    "available": true,
    "method": "Grad-CAM",
    "overlay_path": "/generated/gradcam/gradcam_CR-B2C6154EE2D8_overlay.jpg"
  },
  "segmentation": {
    "available": true,
    "architecture": "U-Net (Deep Learning Segmentation)",
    "affected_percentage": 67.04,
    "leaf_pixels": 59581,
    "diseased_pixels": 39943,
    "overlay_path": "/generated/segmentation/segmentation_CR-B2C6154EE2D8_overlay.jpg"
  },
  "severity": {
    "available": true,
    "severity": "Severe",
    "affected_area_percent": 67.04,
    "disclaimer": "Project-defined initial thresholds; agronomic validation required."
  },
  "traceability": {
    "report_id": "CR-B2C6154EE2D8",
    "segmentation_model": {
      "name": "unet_plantseg",
      "model_hash": "622ac75ee8c7c12e7701384946540e1654a7073c111521f7c2cbadb433b895c8",
      "runtime_format": "SavedModel",
      "source_model_hash": "11eaadaea1723edb86fca13bc4aade6a483f37e75b4d6658390cb63479221145",
      "source_format": "Keras"
    },
    "blockchain": {
      "enabled": true,
      "block_index": 1056,
      "current_hash": "155a404691126191...",
      "chain_valid": true
    }
  }
}
```

---

## 3. Human Review Queue Endpoints

### `GET /review-queue`
Retrieve items currently queued for agronomist confirmation.

- **Authentication**: Required (`review_reports` permission)
- **Query Params**:
  - `status`: Filter by status (`pending`, `resolved`)
- **Response `200 OK`**:
```json
{
  "success": true,
  "items": [
    {
      "review_id": "REV-8A3F2C1D9E0B",
      "report_id": "CR-B2C6154EE2D8",
      "status": "pending",
      "priority": "high",
      "reasons": ["crop_prediction_uncertain"],
      "created_at": "2026-10-01T12:27:40Z"
    }
  ]
}
```

### `POST /review-queue/submit`
Manually flag an assessment report for specialist review.

- **Request Body**:
```json
{
  "report_id": "CR-B2C6154EE2D8",
  "reason": "Foliar spotting atypical for local cultivar."
}
```

### `POST /review-queue/{review_id}/resolve`
Resolve an edge-case diagnosis and commit auditor findings into the evidence chain.

- **Path Parameter**: `review_id` (e.g. `REV-8A3F2C1D9E0B`)
- **Request Body**:
```json
{
  "decision": "confirmed",
  "notes": "Verified Alternaria solani target-board concentric markings."
}
```
- **Allowed Decisions**: `confirmed`, `rejected`, `needs_more_evidence`

---

## 4. Evidence Chain & Traceability Endpoints

### `GET /traceability/status`
Returns high-level statistics of the local evidence chain.
- **Response**: Current block height, head hash, timestamp of latest anchor.

### `GET /traceability/verify`
Performs an on-demand, full cryptographic verification of parent-hash continuity across all blocks from Genesis (#0) to Head.
```json
{
  "valid": true,
  "total_blocks": 1057,
  "invalid_block": null,
  "verified_at": "2026-10-01T12:35:00Z"
}
```

### `GET /traceability/report/{report_id}`
Fetch the immutable evidence record for a specific diagnosis, including any subsequent human review resolution history.

---

## 5. Protected Binary Asset Endpoints

- `GET /uploads/{filename}`: Retrieve original submitted image. Protected by Bearer authentication and path-traversal guards.
- `GET /generated/{subpath:path}`: Retrieve generated Grad-CAM heatmaps, segmentation masks, and composite visualizations. Protected by authentication.
- `POST /admin/cleanup`: Purge transient uploaded/generated assets older than `max_age_hours` (Admin only).
