# Harvest Harbor — Model Lineage, Provenance & Scientific Disclaimers

This document provides complete traceability, training provenance, and cryptographic fingerprints for all machine learning models integrated into the Harvest Harbor agricultural decision-support platform.

---

## 1. Cryptographic Fingerprint Registry (SHA-256)

### Production Runtime Models
| Model Function | Format | Runtime Artifact Path | SHA-256 Digest |
| :--- | :--- | :--- | :--- |
| **Lesion Segmentation (Production Runtime)** | **TensorFlow SavedModel** | `backend/segmentation_model/unet_plantseg_savedmodel/` | `622ac75ee8c7c12e7701384946540e1654a7073c111521f7c2cbadb433b895c8` |
| **Lesion Segmentation (Source Lineage)** | Keras 3 Archive | `backend/segmentation_model/unet_plantseg.keras` | `11eaadaea1723edb86fca13bc4aade6a483f37e75b4d6658390cb63479221145` |
| **Health Screening Gate** | Keras / H5 Dual | `backend/health_model/health_disease_efficientnetb0.keras` | `bb961155086400507012b3d5202c585ee54289bcbbffcbc3baa4abed585689f5` |
| **Botanical Crop Identifier** | Keras / H5 Dual | `backend/crop_model/crop_efficientnetb0.keras` | `b473ae77ca426e6910ec76d40c640732d30eb02c98cf3cee941b56b573a0d331` |
| **Multi-Class Disease Classifier** | Keras / H5 Dual | `backend/model/plantwild_v2_efficientnetb0.keras` | `411611a0977eaba38ae616635ecb8e7f6c1299cb0e9f89f585896786adb6802c` |

### Legacy Environment Compatibility (TensorFlow 2.15 HDF5 Artifacts)
For environments running legacy TensorFlow 2.15 without Keras 3 zip deserializer support, matching standalone HDF5 weight artifacts are provided:
- `backend/health_model/health_disease_efficientnetb0.h5` (`bf459916d7837a9efe4c6100e2849d16ceaeeb0b68e57ecc5e56c0b8682fb097`)
- `backend/crop_model/crop_efficientnetb0.h5` (`c250b1f5504f4326e51fdc781c995d323931db255130964c2f98317a95cb2646`)
- `backend/model/plantwild_v2_efficientnetb0.h5` (`e305ecae717818dcb4401143f362d88fd9b017daa7f57b5488f7918dd90f6ff4`)
- `backend/segmentation_model/unet_plantseg.h5` (`738c1e088acacd7225e2d2f27cc9338a5a3160964e5b71fd45125b49efa95814`)

---

## 2. Model Deep Dive & Lineage

### 2.1 Health Screening Gate
- **Architecture**: EfficientNet-B0 pretrained on ImageNet with custom binary classification top.
- **Classes**:
  - `0`: Healthy
  - `1`: Diseased
- **Balanced Evaluation Benchmark**:
  - Accuracy: $98.65\%$
  - Precision: $100.00\%$
  - Recall: $96.15\%$
  - Macro F1: $98.04\%$
- **Calibration Metadata**:
  - Method: Post-hoc Temperature Scaling
  - Optimal Temperature Parameter: $T = 0.0500$
  - Note: Temperature parameter $T=0.0500$ applies **strictly** to the binary health classifier and must not be conflated with the multi-class disease model.

### 2.2 Dedicated Botanical Crop Classifier
- **Architecture**: EfficientNet-B0 fine-tuned on PlantVillage held-out test split.
- **Classes (14)**: Apple, Blueberry, Cherry, Corn (maize), Grape, Orange, Peach, Bell Pepper, Potato, Raspberry, Soybean, Squash, Strawberry, Tomato.
- **Benchmark Performance (Held-out Test Split)**:
  - Accuracy: $99.94\%$
  - Top-3 Accuracy: $99.98\%$
  - Macro F1: $99.94\%$
- **Scientific Limitation**: These performance figures reflect laboratory held-out test data under controlled benchmark lighting. They **must not** be described as open-field generalization accuracy under uncontrolled outdoor farm environments.

### 2.3 PlantWild v2 Disease Classifier
- **Architecture**: PlantWild v2 Deep Convolutional Neural Network.
- **Scope**: 115 agricultural disease categories.
- **Input Dimensions**: $224 \times 224 \times 3$
- **Calibration**: Softmax probabilities. ECE is **not independently validated**.
- **Provenance Limitation**: Empirical reproduction of the complete 115-class evaluation requires mounting the complete external dataset via `PLANTWILD_DATASET_DIR`. The repository includes verified evaluation on bundled benchmark classes.

### 2.4 U-Net Lesion Segmentation
- **Architecture**: 4-level U-Net deep learning model.
- **Production Runtime**: **TensorFlow SavedModel** directory structure (`saved_model.pb` + `variables/`).
- **Input Signature**: `input_layer` ($256 \times 256 \times 3$, `float32`)
- **Output Signature**: `output_0` ($256 \times 256 \times 1$, `float32`)
- **Evaluation on PlantSeg Test Set (2,295 verified image/mask pairs)**:
  - Mean Intersection-over-Union (IoU): $45.05\%$
  - Dice Coefficient: $57.35\%$
  - Pixel Precision: $60.47\%$
  - Pixel Recall: $68.07\%$

---

## 3. Methodological Disclaimers & UI Honesty

1. **Non-Clinical / Non-Prescriptive Nature**:
   Harvest Harbor is an artificial intelligence decision-support platform designed to assist scouting, prioritization, and agronomic auditability. It does not issue definitive botanical diagnoses or chemical treatment prescriptions. All recommendations must be confirmed by accredited agricultural professionals.
2. **Severity Standard Limitation**:
   Severity categories (Healthy, Early, Moderate, Severe) are project-defined initial thresholds based purely on visual surface coverage geometry ($\frac{\text{diseased pixels}}{\text{leaf pixels}} \times 100$). They have not been cross-validated against university extension or commercial yield-loss damage scales.
3. **Grad-CAM Meaning**:
   Grad-CAM heatmaps illustrate regions where convolutional neural networks detected salient patterns. They represent mathematical gradient attention, not physical or microscopic proof of a live pathogen.
