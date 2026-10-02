# Harvest Harbor — System Architecture & Technical Specification

## 1. High-Level Architectural Overview

Harvest Harbor is an AI-powered agricultural decision-support and audit platform. It couples multi-model deep learning inference (health screening, botanical classification, disease classification, visual explainability, and lesion segmentation) with a tamper-evident, SHA-256 parent-hash-linked evidence chain and an auditable human review resolution workflow.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CLIENT / FRONTEND LAYER                         │
│                           (React 18 + Vite)                            │
│  - Resolution pre-flight validation (dimensions, aspect ratio, size)   │
│  - Reactive UI: Grad-CAM blending, U-Net mask inspector, presets       │
│  - Authenticated asset fetching with secure Blob URL object lifecycle   │
│  - Role-Based Access Control (Farmer, Agronomist, Auditor, Admin)      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ TLS / HTTPS REST API
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        API & SECURITY GATEWAY                          │
│                               (FastAPI)                                │
│  - Request rate limiting & inference concurrency semaphore             │
│  - Security Headers: CSP, Permissions-Policy, X-Content-Type-Options    │
│  - Auth Guard: Bearer Token / X-API-Key + X-User-Role validation       │
│  - Upload Sanitization: Extension whitelist, MIME verify, 50MP ceiling │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     NEURAL INFERENCE PIPELINE                          │
│                                                                        │
│  1. Health Gate (EfficientNet-B0) ──────────────────────────┐          │
│     Binary healthy vs. diseased screening                   │          │
│     Temperature Scaling: T = 0.0500                         │          │
│                                                             ▼          │
│  2. Botanical Classifier (EfficientNet-B0) ───────► Healthy Screening  │
│     14 crop families (Tomato, Potato, Corn, etc.)   Assessments Only   │
│     Host-pathogen validation guard                  (Suppresses Rx)    │
│                                                             │          │
│  3. Disease Classifier (PlantWild v2) ◄─────────────────────┘          │
│     115 disease categories (Softmax probabilities)                     │
│     Host compatibility matrix filtering                                │
│                                                                        │
│  4. Visual Explainability (Grad-CAM)                                   │
│     Gradient activation maps from EfficientNet-B0 top_activation       │
│                                                                        │
│  5. Lesion Segmentation (Production SavedModel U-Net)                  │
│     Input: 256×256×3 ──► Output: 256×256×1 Lesion Mask                 │
│     Quantitative Surface Area %: (Diseased Pixels / Leaf Pixels) × 100 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    AUDIT & TRACEABILITY LAYER                          │
│                                                                        │
│  - Local Tamper-Evident SHA-256 Hash Chain (Parent-hash linking)       │
│  - OS-level file locking (fcntl / portalocker) for atomic append       │
│  - Human Review Queue with reviewer cryptographic identity binding     │
│  - Snapshot immutability: Reports, heatmaps, masks, and audit logs     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Neural Network Pipelines & Mathematical Formulations

### 2.1 Health Screening Gate
- **Architecture**: Transfer-learned EfficientNet-B0 with frozen feature extraction backbone and customized dense classification head.
- **Task**: Binary classification ($\mathcal{Y} \in \{0: \text{healthy}, 1: \text{diseased}\}$).
- **Temperature Scaling**: Logits $z$ are calibrated via empirical temperature parameter $T = 0.0500$:
  $$\hat{p}_i = \frac{e^{z_i / T}}{\sum_{j} e^{z_j / T}}$$
- **Safety Gate Behavior**: If $\hat{p}_{\text{healthy}} \ge 0.50$, subsequent disease interventions are suppressed and the sample transitions to the *Healthy Plant Assessment* pathway, preventing false-positive chemical treatment recommendations.

### 2.2 Botanical Crop Classifier
- **Architecture**: EfficientNet-B0 fine-tuned on 14 agricultural crop families.
- **Classes**: Apple, Blueberry, Cherry, Corn (maize), Grape, Orange (Citrus), Peach, Bell Pepper, Potato, Raspberry, Soybean, Squash, Strawberry, Tomato.
- **Uncertainty Rejection**: If top-1 crop identification confidence is $< 50\%$, disease candidate validation is suspended (`validation.status = "skipped_low_crop_confidence"`), preventing invalid host-pathogen associations.

### 2.3 Disease Classifier & Botanical Compatibility Guard
- **Architecture**: PlantWild v2 deep convolutional neural network.
- **Output**: 115 agricultural disease categories.
- **Compatibility Matrix**: Validates candidate disease against known biological host capabilities. If the candidate pathogen cannot biologically infect the predicted crop host (e.g., Apple Scab on a Tomato leaf), the candidate is rejected (`validation.status = "rejected"`), primary prediction is nullified, and the record is flagged for agronomist review.

### 2.4 Grad-CAM Visual Explainability
- **Target Layer**: `top_activation` of EfficientNet-B0.
- **Methodology**: Computes gradients of the target class score $y^c$ with respect to feature activation maps $A^k$:
  $$\alpha_k^c = \frac{1}{Z} \sum_{i} \sum_{j} \frac{\partial y^c}{\partial A_{i,j}^k}$$
  $$L_{\text{Grad-CAM}}^c = \text{ReLU}\left(\sum_k \alpha_k^c A^k\right)$$
- The resulting heatmap is bilinearly upsampled to the input image resolution ($224 \times 224$), colormapped via Jet, and alpha-blended over the leaf RGB channels.

### 2.5 Lesion Segmentation (U-Net)
- **Architecture**: 4-stage encoder-decoder U-Net with skip connections.
  - Encoder: Repeated blocks of Conv2D ($3 \times 3$, ReLU) $\rightarrow$ BatchNormalization $\rightarrow$ MaxPooling2D ($2 \times 2$).
  - Bottleneck: Conv2D ($256$ filters) with $0.20$ spatial dropout.
  - Decoder: Conv2DTranspose ($2 \times 2$) concatenated with corresponding encoder skip connections $\rightarrow$ Conv2D $\rightarrow$ BatchNormalization.
  - Final Layer: Conv2D ($1 \times 1$, Sigmoid activation) outputting a continuous probability map $[0.0, 1.0]$.
- **Loss Function**: Combined Binary Cross-Entropy and Dice Loss:
  $$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{BCE}} + (1 - \text{Dice Score})$$
  $$\text{Dice} = \frac{2 |P \cap G| + \epsilon}{|P| + |G| + \epsilon}$$

---

## 3. Quantitative Severity Estimation Engine

Severity is computed using two-stage digital leaf geometry:
1. **Leaf Foreground Mask**: Extracted via adaptive HSV + Lab color space thresholding to isolate leaf surface from background soil or bench surfaces.
2. **Lesion Mask**: Inferred by U-Net deep learning model ($256 \times 256$).
3. **Affected Blade Ratio**:
   $$\text{Affected Area \%} = \min\left(100.0, \frac{\text{Diseased Pixels}}{\text{Leaf Pixels}} \times 100.0\right)$$
4. **Project-Defined Severity Tiers**:
   - **Healthy**: $\le 0.0\%$
   - **Early Stage**: $> 0.0\%$ and $< 15.0\%$
   - **Moderate Stage**: $\ge 15.0\%$ and $< 35.0\%$
   - **Severe Stage**: $\ge 35.0\%$
   *(Note: These are project-defined initial thresholds; they are not agronomist-standardized or yield-calibrated).*

---

## 4. Tamper-Evident SHA-256 Evidence Chain

Harvest Harbor enforces end-to-end auditability using a local cryptographic hash-linked evidence chain:
- **Canonical Serialization**: Record attributes are serialized into sorted, whitespace-normalized JSON strings before hashing.
- **Parent Hash Linking**:
  $$H_i = \text{SHA-256}(\text{BlockIndex}_i \,\|\, \text{Timestamp}_i \,\|\, \text{ReportID}_i \,\|\, \text{ImageHash}_i \,\|\, H_{i-1} \,\|\, \text{Data}_i)$$
- **Genesis Block**: Block #0 anchored at system inception.
- **Concurrency & Integrity**: Protected by file-system locks (`fcntl.flock`) to prevent race conditions during concurrent multi-user submissions.
- **Verification Routine**: `verify_chain()` walks the block history from genesis to head, recalculating every SHA-256 hash and ensuring strict parent-linkage continuity.
