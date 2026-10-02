# Harvest Harbor — Technical Documentation Suite

Welcome to the comprehensive technical documentation suite for **Harvest Harbor (Crop Disease AI)**.

---

## Documentation Index

1. **[System Architecture & Specification](ARCHITECTURE.md)**
   - High-level multi-tiered platform architecture.
   - Deep learning inference pipeline (Health Screening, Botanical Classification, PlantWild v2, Grad-CAM, U-Net).
   - Mathematical formulations (Dice + BCE loss, Temperature Scaling, Grad-CAM gradients).
   - Digital leaf geometry & quantitative severity calculation.
   - Tamper-evident SHA-256 evidence chain parent-hash linking and concurrency.

2. **[REST API Reference & Integration Guide](API_REFERENCE.md)**
   - Security headers, Bearer tokens, and RBAC matrix.
   - Diagnostics endpoints (`POST /predict`).
   - Human review workflow (`/review-queue`, `/review-queue/submit`, `/review-queue/{review_id}/resolve`).
   - Cryptographic evidence chain verification (`/traceability/verify`, `/traceability/report/{report_id}`).
   - Binary asset retrieval & administrative cleanup endpoints.

3. **[Model Lineage & Scientific Provenance](MODEL_LINEAGE.md)**
   - Cryptographic SHA-256 fingerprint registry for all neural network weights.
   - Production runtime SavedModel (`unet_plantseg_savedmodel`) vs. source Keras lineage.
   - Dataset sources (PlantVillage 14 crops, PlantWild v2 115 categories, PlantSeg).
   - Temperature scaling calibration metadata ($T = 0.0500$ for binary health screening).
   - Explicit scientific disclaimers and limitations.

4. **[Deployment & Operations Manual](DEPLOYMENT_AND_OPERATIONS.md)**
   - Hardware requirements and software dependencies.
   - Environment variables & security configuration.
   - Systemd service configurations and Nginx reverse proxy architecture.
   - Evidence chain backup strategies and automated file maintenance.

---

## Quick Reference Links
- Root Overview: [Project README](../README.md)
- Backend Source: [backend/](../backend/)
- Frontend Source: [frontend/](../frontend/)
