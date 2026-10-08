# Empirical Research Evaluation & Scientific Benchmarks

**Harvest Harbor: An Interpretable, Calibrated, and Traceable AI Platform for Precision Crop Pathology**

This document provides empirical evaluations, mathematical formulations, confusion matrices, and publication-ready tables based on real evaluations conducted against the official held-out test sets.

---

## 1. System Performance Summary

All evaluations were executed on the production model weights packaged with Harvest Harbor.

| Subsystem | Architecture | Metric | Empirical Value | Evaluation Dataset / Test Split |
|---|---|---|---|---|
| **Binary Health Screening** | EfficientNet-B0 | Accuracy | **100.00%** | PlantVillage Held-Out Test ($N=50$) |
| | | Precision | **100.00%** | Balanced Healthy vs Diseased |
| | | Recall (Sensitivity) | **100.00%** | Balanced Healthy vs Diseased |
| | | F1-Score | **100.00%** | Balanced Healthy vs Diseased |
| **Dedicated Crop Classifier** | EfficientNet-B0 | Top-1 Accuracy | **100.00%** | Held-Out Test Split ($N=140$, 14 Crops) |
| | | Top-3 Accuracy | **100.00%** | 10 Samples Per Crop Class |
| **U-Net Lesion Segmentation** | U-Net (256×256) | Mean IoU (Jaccard) | **44.30%** | PlantSeg Benchmark Test Set ($N=50$) |
| | | Mean Dice (F1) | **55.52%** | Pixel-Level Lesion Ground Truth |
| | | Pixel Precision | **61.33%** | Lesion Segmentation Mask |
| | | Pixel Recall | **65.22%** | Lesion Segmentation Mask |
| **Foliar Severity Tiering** | Area Ratio Formulation | Tier Classification Acc | **52.00%** | PlantSeg Ground Truth vs Predicted Tiers |
| | | Mean Absolute Error (MAE) | **13.95%** | Absolute Leaf Area Deviation |
| **Confidence Calibration** | Temperature Scaling | Uncalibrated ECE ($T=1.0$) | **2.30%** | Expected Calibration Error |
| | | Calibrated ECE ($T=0.05$) | **1.00%** | Expected Calibration Error Reduction |

---

## 2. Dedicated Crop Classifier Confusion Matrix ($14 \times 14$)

The dedicated crop classifier was evaluated across all 14 crop families on the held-out test split ($N=140$, balanced 10 test samples per class).

**Figure Reference**: [figures/fig1_crop_confusion_matrix.png](figures/fig1_crop_confusion_matrix.png) | [Vector SVG](figures/fig1_crop_confusion_matrix.svg)

### Empirical Numerical Matrix:
```
Rows: Ground Truth Class | Columns: Predicted Class (0 to 13)
Classes: ['Apple', 'Blueberry', 'Cherry (including sour)', 'Corn (maize)', 'Grape', 'Orange', 'Peach', 'Pepper, bell', 'Potato', 'Raspberry', 'Soybean', 'Squash', 'Strawberry', 'Tomato']

[[10,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
 [ 0, 10,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
 [ 0,  0, 10,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
 [ 0,  0,  0, 10,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
 [ 0,  0,  0,  0, 10,  0,  0,  0,  0,  0,  0,  0,  0,  0],
 [ 0,  0,  0,  0,  0, 10,  0,  0,  0,  0,  0,  0,  0,  0],
 [ 0,  0,  0,  0,  0,  0, 10,  0,  0,  0,  0,  0,  0,  0],
 [ 0,  0,  0,  0,  0,  0,  0, 10,  0,  0,  0,  0,  0,  0],
 [ 0,  0,  0,  0,  0,  0,  0,  0, 10,  0,  0,  0,  0,  0],
 [ 0,  0,  0,  0,  0,  0,  0,  0,  0, 10,  0,  0,  0,  0],
 [ 0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 10,  0,  0,  0],
 [ 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 10,  0,  0],
 [ 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 10,  0],
 [ 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0, 10]]
```

### LaTeX Table for Paper:
```latex
\begin{table}[htbp]
\centering
\caption{Dedicated Crop Classifier (EfficientNet-B0) Performance on 14 Held-Out Crop Families.}
\label{tab:crop_performance}
\begin{tabular}{lcccc}
\hline
\textbf{Crop Species} & \textbf{Test Samples} & \textbf{Top-1 Acc (\%)} & \textbf{Top-3 Acc (\%)} \\
\hline
Apple & 10 & 100.0 & 100.0 \\
Blueberry & 10 & 100.0 & 100.0 \\
Cherry (including sour) & 10 & 100.0 & 100.0 \\
Corn (maize) & 10 & 100.0 & 100.0 \\
Grape & 10 & 100.0 & 100.0 \\
Orange & 10 & 100.0 & 100.0 \\
Peach & 10 & 100.0 & 100.0 \\
Pepper, bell & 10 & 100.0 & 100.0 \\
Potato & 10 & 100.0 & 100.0 \\
Raspberry & 10 & 100.0 & 100.0 \\
Soybean & 10 & 100.0 & 100.0 \\
Squash & 10 & 100.0 & 100.0 \\
Strawberry & 10 & 100.0 & 100.0 \\
Tomato & 10 & 100.0 & 100.0 \\
\hline
\textbf{Macro Aggregate} & \textbf{140} & \textbf{100.00\%} & \textbf{100.00\%} \\
\hline
\end{tabular}
\end{table}
```

---

## 3. Foliar Severity Tiering & Lesion Segmentation

### 3.1 Severity Confusion Matrix ($4 \times 4$)

Evaluated against pixel-level annotated ground-truth masks from the PlantSeg held-out benchmark ($N=50$).

**Figure Reference**: [figures/fig2_severity_confusion_matrix.png](figures/fig2_severity_confusion_matrix.png) | [Vector SVG](figures/fig2_severity_confusion_matrix.svg)

| Ground Truth \ Predicted | Healthy (0%) | Early (&lt;15%) | Moderate (15–35%) | Severe (&ge;35%) | Total GT |
|---|:---:|:---:|:---:|:---:|:---:|
| **Healthy** | 0 | 3 | 1 | 2 | 6 |
| **Early** | 0 | 13 | 8 | 1 | 22 |
| **Moderate** | 0 | 4 | 4 | 2 | 10 |
| **Severe** | 1 | 1 | 1 | 9 | 12 |
| **Total Predicted** | 1 | 21 | 14 | 14 | 50 |

- **Tier Classification Accuracy**: `52.00%`
- **Mean Absolute Error (MAE)**: `13.95%` of total foliar area
- **Scientific Caveat**: Threshold boundaries (Healthy <= 0%, Early < 15%, Moderate 15-35%, Severe >= 35%) are project-defined initial thresholds. While computed objectively via U-Net lesion pixel integration, they require formal multi-center agronomic field calibration before direct chemical intervention.

### 3.2 U-Net Lesion Segmentation Benchmark

**Figure Reference**: [figures/fig4_segmentation_performance.png](figures/fig4_segmentation_performance.png)

- **Mean Intersection-over-Union (IoU / Jaccard Index)**: `44.30%`
- **Dice Similarity Coefficient ($F_1$)**: `55.52%`
- **Pixel-Level Precision**: `61.33%`
- **Pixel-Level Recall**: `65.22%`

$$\text{IoU} = \frac{|A \cap B|}{|A \cup B|} = \frac{TP}{TP + FP + FN}$$
$$\text{Dice} = \frac{2 |A \cap B|}{|A| + |B|} = \frac{2 TP}{2 TP + FP + FN}$$

---

## 4. Post-Hoc Probability Calibration

Deep neural classifiers frequently suffer from overconfidence. Harvest Harbor incorporates **Temperature Scaling** to calibrate probabilities without modifying model parameters.

**Figure Reference**: [figures/fig5_calibration_reliability_diagram.png](figures/fig5_calibration_reliability_diagram.png)

$$\hat{p}_i = \frac{\exp(z_i / T)}{\sum_j \exp(z_j / T)}$$

Where $z$ denotes raw logits and $T$ is the learned temperature parameter ($T = 0.05$).

- **Uncalibrated Expected Calibration Error ($T=1.0$)**: `2.30%`
- **Calibrated Expected Calibration Error ($T=0.05$)**: `1.00%`
- **Relative ECE Error Reduction**: `56.5%`

---

## 5. Pathology Classification Benchmark (18 Validated Classes)

**Figure Reference**: [figures/fig6_disease_per_class_f1.png](figures/fig6_disease_per_class_f1.png)

Evaluated on the local PlantVillage ground truth benchmark mapping:

| Pathology Diagnosis | Precision (\%) | Recall (\%) | $F_1$-Score (\%) |
|---|:---:|:---:|:---:|
| Apple Black Rot | 42.86 | 100.00 | 60.00 |
| Bell Pepper Bacterial Spot | 50.00 | 33.33 | 40.00 |
| Corn Gray Leaf Spot | 37.50 | 100.00 | 54.55 |
| Grape Black Rot | 100.00 | 33.33 | 50.00 |
| Strawberry Leaf Scorch | 50.00 | 33.33 | 40.00 |
| Tomato Leaf Mold | 100.00 | 50.00 | 66.67 |

---

## 6. Publication Figures Index

All generated figures are stored in `docs/figures/` in publication-grade high-resolution raster format:

1. **Figure 1**: [fig1_crop_confusion_matrix.png](figures/fig1_crop_confusion_matrix.png) — 14×14 Dedicated Crop Classifier Confusion Matrix
2. **Figure 2**: [fig2_severity_confusion_matrix.png](figures/fig2_severity_confusion_matrix.png) — 4×4 Foliar Severity Tier Confusion Matrix
3. **Figure 3**: [fig3_health_confusion_matrix.png](figures/fig3_health_confusion_matrix.png) — 2×2 Binary Health Screening Confusion Matrix
4. **Figure 4**: [fig4_segmentation_performance.png](figures/fig4_segmentation_performance.png) — U-Net Lesion Segmentation Benchmark Metrics
5. **Figure 5**: [fig5_calibration_reliability_diagram.png](figures/fig5_calibration_reliability_diagram.png) — Expected Calibration Error (ECE) Temperature Scaling
6. **Figure 6**: [fig6_disease_per_class_f1.png](figures/fig6_disease_per_class_f1.png) — Per-Class $F_1$-Scores across Pathologies
7. **Figure 7**: [system_block_diagram.png](figures/system_block_diagram.png) — Harvest Harbor System Architecture Block Diagram
8. **Figure 8**: [system_flow_chart.png](figures/system_flow_chart.png) — End-to-End System Flow Chart & Data Lifecycle
