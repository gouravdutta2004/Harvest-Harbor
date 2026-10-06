"""
Harvest Harbor — Publication Block Diagram Generator
====================================================
Generates a comprehensive, publication-grade architectural block diagram
illustrating all multi-tier ML pipelines, gating logic, segmentation,
Grad-CAM explainability, blockchain traceability, and agronomist review.

Outputs:
  - docs/figures/system_block_diagram.svg
  - docs/figures/system_block_diagram.png
  - docs/figures/fig7_system_architecture_pipeline.svg
  - docs/figures/fig7_system_architecture_pipeline.png
  - docs/figures/10_system_block_diagram.svg
  - docs/figures/10_system_block_diagram.png
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def generate_svg(output_path: Path):
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2400 1350" width="2400" height="1350">
  <defs>
    <style>
      .title { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 32px; font-weight: 800; fill: #0f172a; }
      .subtitle { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 16px; font-weight: 500; fill: #64748b; }
      .col-header { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 15px; font-weight: 700; fill: #1e293b; text-transform: uppercase; letter-spacing: 1.5px; }
      .card-title { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 16px; font-weight: 700; }
      .card-sub { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 13px; font-weight: 600; fill: #475569; }
      .card-body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 12px; fill: #334155; line-height: 1.5; }
      .metric-tag { font-family: 'Courier New', monospace; font-size: 11px; font-weight: 700; }
      .arrow { stroke: #94a3b8; stroke-width: 2.5; fill: none; stroke-linecap: round; }
      .arrow-accent { stroke: #10b981; stroke-width: 3; fill: none; stroke-linecap: round; }
      .branch-text { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 12px; font-weight: 700; }
    </style>
    
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#94a3b8" />
    </marker>
    <marker id="arrowhead-emerald" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#10b981" />
    </marker>
    <marker id="arrowhead-rose" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#f43f5e" />
    </marker>
    <marker id="arrowhead-blue" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#3b82f6" />
    </marker>

    <!-- Filters & Shadows -->
    <filter id="shadow" x="-4%" y="-4%" width="108%" height="108%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0f172a" flood-opacity="0.05" />
    </filter>
    <filter id="card-shadow" x="-3%" y="-3%" width="106%" height="106%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#0f172a" flood-opacity="0.04" />
    </filter>
  </defs>

  <!-- Background Canvas -->
  <rect width="2400" height="1350" fill="#f8fafc" />

  <!-- Outer Header Card -->
  <rect x="60" y="40" width="2280" height="100" rx="20" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)" />
  <circle cx="110" cy="90" r="24" fill="#ecfdf5" stroke="#10b981" stroke-width="2" />
  <path d="M 100 90 L 107 97 L 122 82" stroke="#059669" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  
  <text x="150" y="82" class="title">HARVEST HARBOR: END-TO-END MULTI-TIER SYSTEM ARCHITECTURE</text>
  <text x="150" y="112" class="subtitle">Interpretable Foliar Pathology Inference, Temperature Calibration, U-Net Lesion Segmentation, SHA-256 Ledger &amp; Agronomist Triage</text>
  
  <!-- Status Badge on Right -->
  <rect x="2070" y="70" width="230" height="40" rx="12" fill="#f0fdf4" stroke="#86efac" stroke-width="1.5" />
  <circle cx="2095" cy="90" r="6" fill="#22c55e" />
  <text x="2115" y="95" font-family="'Helvetica Neue', sans-serif" font-size="13" font-weight="700" fill="#15803d">PRODUCTION VERIFIED</text>


  <!-- ========================================================================= -->
  <!-- COLUMN 1: INGESTION & PRE-FLIGHT (x: 60, w: 410) -->
  <!-- ========================================================================= -->
  <rect x="60" y="165" width="410" height="1135" rx="24" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)" />
  <rect x="60" y="165" width="410" height="50" rx="24" fill="#f1f5f9" />
  <text x="85" y="196" class="col-header">1. INGESTION &amp; PRE-FLIGHT</text>

  <!-- Specimen Input Box -->
  <rect x="85" y="240" width="360" height="160" rx="16" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" filter="url(#card-shadow)" />
  <rect x="105" y="260" width="40" height="40" rx="10" fill="#e0f2fe" stroke="#38bdf8" stroke-width="1.5" />
  <text x="117" y="286" font-size="20">🍃</text>
  <text x="160" y="280" class="card-title" fill="#0284c7">Foliar Leaf Specimen</text>
  <text x="160" y="300" class="card-sub">Field Camera / Upload</text>
  <text x="105" y="335" class="card-body">• Raw formats: JPEG, PNG, WEBP (Max 15 MB)</text>
  <text x="105" y="355" class="card-body">• Captured foliar blade under daylight illumination</text>
  <text x="105" y="375" class="card-body">• Multipart/form-data with Bearer Token</text>

  <!-- Pre-Flight Quality Guard Box -->
  <rect x="85" y="440" width="360" height="220" rx="16" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" filter="url(#card-shadow)" />
  <rect x="105" y="460" width="40" height="40" rx="10" fill="#fef3c7" stroke="#f59e0b" stroke-width="1.5" />
  <text x="117" y="486" font-size="20">🛡️</text>
  <text x="160" y="480" class="card-title" fill="#d97706">Pre-Flight Quality Guard</text>
  <text x="160" y="500" class="card-sub">Deterministic Input Validation</text>
  <text x="105" y="535" class="card-body">• Magic Byte &amp; MIME validation (Strict image check)</text>
  <text x="105" y="555" class="card-body">• Max decoded pixel cap: 50 MP (DoS/Bomb Guard)</text>
  <text x="105" y="575" class="card-body">• Min geometry check: 32×32 px (Blur filter)</text>
  <text x="105" y="595" class="card-body">• Safe path sanitization &amp; filename hashing</text>
  <rect x="105" y="615" width="320" height="28" rx="8" fill="#fef9c3" />
  <text x="115" y="634" class="metric-tag" fill="#854d0e">PASS: Stream split to CNN &amp; U-Net formats</text>

  <!-- Preprocessing & Normalization Box -->
  <rect x="85" y="700" width="360" height="190" rx="16" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" filter="url(#card-shadow)" />
  <rect x="105" y="720" width="40" height="40" rx="10" fill="#f1f5f9" stroke="#94a3b8" stroke-width="1.5" />
  <text x="117" y="746" font-size="20">⚙️</text>
  <text x="160" y="740" class="card-title" fill="#334155">Dual-Stream Resizing</text>
  <text x="160" y="760" class="card-sub">Color &amp; Tensor Normalization</text>
  <text x="105" y="795" class="card-body">• Stream A: 224×224×3 RGB (EfficientNet-B0)</text>
  <text x="105" y="815" class="card-body">• Stream B: 256×256×3 RGB (U-Net PlantSeg)</text>
  <text x="105" y="835" class="card-body">• ImageNet Mean/Std Normalization: [0, 1]</text>
  <text x="105" y="855" class="card-body">• Non-blocking executor dispatch: run_in_executor</text>

  <!-- Non-Blocking Async Worker -->
  <rect x="85" y="930" width="360" height="140" rx="16" fill="#f0fdf4" stroke="#86efac" stroke-width="1.5" filter="url(#card-shadow)" />
  <text x="105" y="965" class="card-title" fill="#15803d">Async Executor Slots</text>
  <text x="105" y="985" class="card-sub">FastAPI Concurrency Core</text>
  <text x="105" y="1015" class="card-body">• Max 4 concurrent ML workers via Semaphore</text>
  <text x="105" y="1035" class="card-body">• Zero event-loop starvation under high RPS</text>
  <text x="105" y="1055" class="card-body">• Per-IP sliding-window rate limit: 100 req/min</text>


  <!-- ========================================================================= -->
  <!-- COLUMN 2: TIER-1 HEALTH SCREENING (x: 520, w: 420) -->
  <!-- ========================================================================= -->
  <rect x="520" y="165" width="420" height="1135" rx="24" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)" />
  <rect x="520" y="165" width="420" height="50" rx="24" fill="#f1f5f9" />
  <text x="545" y="196" class="col-header">2. TIER-1 HEALTH SCREENING</text>

  <!-- Binary EfficientNet-B0 Classifier -->
  <rect x="545" y="240" width="370" height="230" rx="16" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" filter="url(#card-shadow)" />
  <rect x="565" y="260" width="40" height="40" rx="10" fill="#ecfdf5" stroke="#10b981" stroke-width="1.5" />
  <text x="577" y="286" font-size="20">🔬</text>
  <text x="620" y="280" class="card-title" fill="#059669">Binary Health Classifier</text>
  <text x="620" y="300" class="card-sub">EfficientNet-B0 (Foliar Screening)</text>
  <text x="565" y="335" class="card-body">• Architecture: EfficientNet-B0 backbone</text>
  <text x="565" y="355" class="card-body">• Classes: Healthy ($C_0$) vs. Diseased ($C_1$)</text>
  <text x="565" y="375" class="card-body">• Accuracy: 100.00% (PlantVillage Test Split)</text>
  <text x="565" y="395" class="card-body">• Precision: 100.00% | Recall: 100.00% | F1: 1.00</text>
  <rect x="565" y="415" width="330" height="35" rx="8" fill="#dcfce7" />
  <text x="575" y="437" class="metric-tag" fill="#166534">EVAL: Acc 100% | Sens 100% | Spec 100%</text>

  <!-- Post-Hoc Temperature Scaling -->
  <rect x="545" y="500" width="370" height="200" rx="16" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" filter="url(#card-shadow)" />
  <rect x="565" y="520" width="40" height="40" rx="10" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5" />
  <text x="577" y="546" font-size="20">📐</text>
  <text x="620" y="540" class="card-title" fill="#1d4ed8">Confidence Calibration</text>
  <text x="620" y="560" class="card-sub">Post-Hoc Temperature Scaling</text>
  <text x="565" y="595" class="card-body">• Formulation: p̂ = softmax(z / T), T = 0.05</text>
  <text x="565" y="615" class="card-body">• Uncalibrated ECE (T=1.0): 2.30%</text>
  <text x="565" y="635" class="card-body">• Calibrated ECE (T=0.05): 1.00% (56.5% reduction)</text>
  <rect x="565" y="655" width="330" height="28" rx="8" fill="#dbeafe" />
  <text x="575" y="674" class="metric-tag" fill="#1e40af">ECE: 2.30% → 1.00% (Reliable Probabilities)</text>

  <!-- Health Gating Decision Diamond / Split -->
  <rect x="545" y="730" width="370" height="150" rx="16" fill="#fff7ed" stroke="#fdba74" stroke-width="1.5" filter="url(#card-shadow)" />
  <text x="565" y="765" class="card-title" fill="#c2410c">Confidence Gating Logic</text>
  <text x="565" y="785" class="card-sub">Binary Branch Decision</text>
  <text x="565" y="815" class="card-body">• If Healthy &amp; Conf ≥ 60%: Trigger Healthy Exit</text>
  <text x="565" y="835" class="card-body">• If Diseased &amp; Conf ≥ 50%: Advance to Tiers 2–5</text>
  <text x="565" y="855" class="card-body">• If Uncertain (Conf &lt; 60%): Escalate to Review Queue</text>

  <!-- Healthy Exit Card -->
  <rect x="545" y="910" width="370" height="180" rx="16" fill="#ecfdf5" stroke="#a7f3d0" stroke-width="1.5" filter="url(#card-shadow)" />
  <rect x="565" y="930" width="36" height="36" rx="10" fill="#d1fae5" />
  <text x="575" y="955" font-size="18">🏆</text>
  <text x="615" y="950" class="card-title" fill="#047857">Healthy Branch Exit</text>
  <text x="615" y="970" class="card-sub">Disease Diagnosis Suppressed</text>
  <text x="565" y="1005" class="card-body">• Issues Healthy Plant Certificate with SHA-256 seal</text>
  <text x="565" y="1025" class="card-body">• Recommends Good Agricultural Practices (GAP)</text>
  <text x="565" y="1045" class="card-body">• Suppresses false-positive disease protocols</text>
  <text x="565" y="1065" class="card-body">• Records audit proof on immutable blockchain</text>


  <!-- ========================================================================= -->
  <!-- COLUMN 3: TIER-2 & 3 TAXONOMY & PATHOLOGY (x: 990, w: 420) -->
  <!-- ========================================================================= -->
  <rect x="990" y="165" width="420" height="1135" rx="24" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)" />
  <rect x="990" y="165" width="420" height="50" rx="24" fill="#f1f5f9" />
  <text x="1015" y="196" class="col-header">3. TAXONOMY &amp; PATHOLOGY</text>

  <!-- Dedicated Crop Classifier -->
  <rect x="1015" y="240" width="370" height="230" rx="16" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" filter="url(#card-shadow)" />
  <rect x="1035" y="260" width="40" height="40" rx="10" fill="#f0fdf4" stroke="#4ade80" stroke-width="1.5" />
  <text x="1047" y="286" font-size="20">🌱</text>
  <text x="1090" y="280" class="card-title" fill="#16a34a">Crop Species Classifier</text>
  <text x="1090" y="300" class="card-sub">14-Class Botanical EfficientNet-B0</text>
  <text x="1035" y="335" class="card-body">• 14 Crop Taxa: Apple, Corn, Grape, Potato, Tomato...</text>
  <text x="1035" y="355" class="card-body">• Top-1 Accuracy: 100.00% (N=140 held-out split)</text>
  <text x="1035" y="375" class="card-body">• Top-3 Accuracy: 100.00% | Zero Cross-Crop Drift</text>
  <text x="1035" y="395" class="card-body">• Provides botanical prior for compatibility gate</text>
  <rect x="1035" y="415" width="330" height="35" rx="8" fill="#dcfce7" />
  <text x="1045" y="437" class="metric-tag" fill="#15803d">EVAL: 14/14 Crops 100% Precision &amp; Recall</text>

  <!-- PlantWild-v2 Disease Classifier -->
  <rect x="1015" y="500" width="370" height="230" rx="16" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" filter="url(#card-shadow)" />
  <rect x="1035" y="520" width="40" height="40" rx="10" fill="#fef2f2" stroke="#f87171" stroke-width="1.5" />
  <text x="1047" y="546" font-size="20">🦠</text>
  <text x="1090" y="540" class="card-title" fill="#dc2626">PlantWild-v2 Classifier</text>
  <text x="1090" y="560" class="card-sub">115-Class Pathology Network</text>
  <text x="1035" y="595" class="card-body">• 115 Foliar Pathologies &amp; Health Categories</text>
  <text x="1035" y="615" class="card-body">• Deep feature extraction via top_activation layer</text>
  <text x="1035" y="635" class="card-body">• Uncalibrated Top-3 ranked candidate probabilities</text>
  <text x="1035" y="655" class="card-body">• Outputs raw logits vector across 115 classes</text>
  <rect x="1035" y="675" width="330" height="35" rx="8" fill="#fee2e2" />
  <text x="1045" y="697" class="metric-tag" fill="#991b1b">OUTPUT: Unfiltered 115-Class Logits Vector</text>

  <!-- Crop-Aware Compatibility Gating Matrix -->
  <rect x="1015" y="760" width="370" height="250" rx="16" fill="#faf5ff" stroke="#d8b4fe" stroke-width="1.5" filter="url(#card-shadow)" />
  <rect x="1035" y="780" width="40" height="40" rx="10" fill="#f3e8ff" stroke="#c084fc" stroke-width="1.5" />
  <text x="1047" y="806" font-size="20">🔒</text>
  <text x="1090" y="800" class="card-title" fill="#7e22ce">Compatibility Gating Filter</text>
  <text x="1090" y="820" class="card-sub">Crop-Aware Masking Matrix</text>
  <text x="1035" y="855" class="card-body">• Cross-references Predicted Crop $\times$ Disease Domain</text>
  <text x="1035" y="875" class="card-body">• Zeroes out cross-family anomalies:</text>
  <text x="1035" y="895" class="card-body">  e.g. Suppresses Apple Scab if leaf is Tomato</text>
  <text x="1035" y="915" class="card-body">• Renormalizes filtered distribution over valid set</text>
  <text x="1035" y="935" class="card-body">• Preserves raw candidate tail for audit transparency</text>
  <rect x="1035" y="955" width="330" height="35" rx="8" fill="#f3e8ff" />
  <text x="1045" y="977" class="metric-tag" fill="#6b21a8">RESULT: Robust Agronomic Top-3 Diagnosis</text>

  <!-- Agronomic Advisory Linking -->
  <rect x="1015" y="1040" width="370" height="180" rx="16" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" filter="url(#card-shadow)" />
  <text x="1035" y="1075" class="card-title" fill="#0f172a">19-Disease Knowledge Base</text>
  <text x="1035" y="1095" class="card-sub">Agronomic Action Plan Generator</text>
  <text x="1035" y="1125" class="card-body">• Curated agronomic markdown profiles</text>
  <text x="1035" y="1145" class="card-body">• Cultural controls, chemical timing, bio-fungicides</text>
  <text x="1035" y="1165" class="card-body">• Integrated Pest Management (IPM) adherence</text>


  <!-- ========================================================================= -->
  <!-- COLUMN 4: TIER-4 & 5 SEGMENTATION & GRAD-CAM (x: 1460, w: 420) -->
  <!-- ========================================================================= -->
  <rect x="1460" y="165" width="420" height="1135" rx="24" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)" />
  <rect x="1460" y="165" width="420" height="50" rx="24" fill="#f1f5f9" />
  <text x="1485" y="196" class="col-header">4. SEGMENTATION &amp; EXPLAINABILITY</text>

  <!-- Deep U-Net Segmentation -->
  <rect x="1485" y="240" width="370" height="240" rx="16" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" filter="url(#card-shadow)" />
  <rect x="1505" y="260" width="40" height="40" rx="10" fill="#f5f3ff" stroke="#a78bfa" stroke-width="1.5" />
  <text x="1517" y="286" font-size="20">🎯</text>
  <text x="1560" y="280" class="card-title" fill="#6d28d9">U-Net Lesion Segmenter</text>
  <text x="1560" y="300" class="card-sub">Encoder-Decoder with Skip Connections</text>
  <text x="1505" y="335" class="card-body">• Input Tensor: 256×256×3 RGB (SavedModel)</text>
  <text x="1505" y="355" class="card-body">• Mean IoU (Jaccard Index): 44.30% (PlantSeg N=50)</text>
  <text x="1505" y="375" class="card-body">• Mean Dice Coefficient (F1): 55.52%</text>
  <text x="1505" y="395" class="card-body">• Pixel Precision: 61.33% | Pixel Recall: 65.22%</text>
  <text x="1505" y="415" class="card-body">• Pixel Mask: Background vs Blade vs Lesion</text>
  <rect x="1505" y="430" width="330" height="35" rx="8" fill="#ede9fe" />
  <text x="1515" y="452" class="metric-tag" fill="#5b21b6">BENCHMARK: Mean IoU 44.30% | Dice 55.52%</text>

  <!-- Severity Quantification Engine -->
  <rect x="1485" y="510" width="370" height="230" rx="16" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" filter="url(#card-shadow)" />
  <rect x="1505" y="530" width="40" height="40" rx="10" fill="#fff1f2" stroke="#fb7185" stroke-width="1.5" />
  <text x="1517" y="556" font-size="20">📊</text>
  <text x="1560" y="550" class="card-title" fill="#e11d48">Severity Tiering Engine</text>
  <text x="1560" y="570" class="card-sub">Quantitative Pixel Ratio Formulation</text>
  <text x="1505" y="605" class="card-body">• Formulation: Severity = (Σ P_lesion / Σ P_leaf) × 100%</text>
  <text x="1505" y="625" class="card-body">• Mean Absolute Error (MAE): 13.95% foliar area</text>
  <text x="1505" y="645" class="card-body">• Tier Classification Accuracy: 52.00%</text>
  <text x="1505" y="665" class="card-body">• Tiers: Healthy (0%), Early (&lt;15%),</text>
  <text x="1505" y="685" class="card-body">  Moderate (15–35%), Severe (≥35%)</text>
  <rect x="1505" y="700" width="330" height="30" rx="8" fill="#ffe4e6" />
  <text x="1515" y="720" class="metric-tag" fill="#be123c">MAE: 13.95% | 4-Tier Categorization</text>

  <!-- Grad-CAM Visual Explainability -->
  <rect x="1485" y="770" width="370" height="230" rx="16" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" filter="url(#card-shadow)" />
  <rect x="1505" y="790" width="40" height="40" rx="10" fill="#fdf4ff" stroke="#f472b6" stroke-width="1.5" />
  <text x="1517" y="816" font-size="20">👁️</text>
  <text x="1560" y="810" class="card-title" fill="#c026d3">Grad-CAM Explainability</text>
  <text x="1560" y="830" class="card-sub">Foliar Attention Attribution</text>
  <text x="1505" y="865" class="card-body">• Target Layer: top_activation (EfficientNet-B0)</text>
  <text x="1505" y="885" class="card-body">• Gradient of target pathology w.r.t feature maps</text>
  <text x="1505" y="905" class="card-body">• Generates normalized colormap overlay (JET/TURBO)</text>
  <text x="1505" y="925" class="card-body">• Verifies model visual focus on genuine lesions</text>
  <rect x="1505" y="945" width="330" height="35" rx="8" fill="#fae8ff" />
  <text x="1515" y="967" class="metric-tag" fill="#86198f">INTERPRETABILITY: Grounded Heatmap Overlay</text>

  <!-- Multi-Modal Visual Output Display -->
  <rect x="1485" y="1030" width="370" height="190" rx="16" fill="#f0fdfa" stroke="#5eead4" stroke-width="1.5" filter="url(#card-shadow)" />
  <text x="1505" y="1065" class="card-title" fill="#0f766e">Visual Inspection Stream</text>
  <text x="1505" y="1085" class="card-sub">Tri-View Diagnostic Presentation</text>
  <text x="1505" y="1115" class="card-body">• View 1: Original High-Resolution Specimen</text>
  <text x="1505" y="1135" class="card-body">• View 2: Grad-CAM Saliency Heatmap Overlay</text>
  <text x="1505" y="1155" class="card-body">• View 3: U-Net Folium &amp; Lesion Segment Mask</text>
  <text x="1505" y="1175" class="card-body">• Interactive opacity &amp; toggle controls</text>


  <!-- ========================================================================= -->
  <!-- COLUMN 5: TIER-6 & 7 TRUST, LEDGER & TRIAGE (x: 1930, w: 410) -->
  <!-- ========================================================================= -->
  <rect x="1930" y="165" width="410" height="1135" rx="24" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)" />
  <rect x="1930" y="165" width="410" height="50" rx="24" fill="#f1f5f9" />
  <text x="1955" y="196" class="col-header">5. TRUST, AUDIT &amp; TRIAGE</text>

  <!-- SHA-256 Blockchain Ledger -->
  <rect x="1955" y="240" width="360" height="260" rx="16" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" filter="url(#card-shadow)" />
  <rect x="1975" y="260" width="40" height="40" rx="10" fill="#f1f5f9" stroke="#64748b" stroke-width="1.5" />
  <text x="1987" y="286" font-size="20">🔗</text>
  <text x="2030" y="280" class="card-title" fill="#0f172a">SHA-256 Evidence Ledger</text>
  <text x="2030" y="300" class="card-sub">Tamper-Evident Audit Chain</text>
  <text x="1975" y="335" class="card-body">• Genesis Block &amp; Canonical Cryptographic Hashes</text>
  <text x="1975" y="355" class="card-body">• H_n = SHA-256(H_{n-1} || Report ID || Metadata)</text>
  <text x="1975" y="375" class="card-body">• File-locking concurrency (zero race conditions)</text>
  <text x="1975" y="395" class="card-body">• Records model weights hash, inputs &amp; decisions</text>
  <text x="1975" y="415" class="card-body">• 100% Cryptographic Verification Endpoint</text>
  <rect x="1975" y="435" width="320" height="35" rx="8" fill="#e2e8f0" />
  <text x="1985" y="457" class="metric-tag" fill="#1e293b">INTEGRITY: SHA-256 Tamper-Evident Ledger</text>

  <!-- Agronomist Human Review Queue -->
  <rect x="1955" y="530" width="360" height="260" rx="16" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" filter="url(#card-shadow)" />
  <rect x="1975" y="550" width="40" height="40" rx="10" fill="#fef3c7" stroke="#fbbf24" stroke-width="1.5" />
  <text x="1987" y="576" font-size="20">👨‍🌾</text>
  <text x="2030" y="570" class="card-title" fill="#b45309">Agronomist Review Queue</text>
  <text x="2030" y="590" class="card-sub">Human-in-the-Loop Clinical Triage</text>
  <text x="1975" y="625" class="card-body">• Auto-Escalation triggers: High severity (≥35%),</text>
  <text x="1975" y="645" class="card-body">  low confidence, or crop-disease conflict</text>
  <text x="1975" y="665" class="card-body">• Priority Queuing: CRITICAL, HIGH, NORMAL</text>
  <text x="1975" y="685" class="card-body">• Agronomist override: Confirm, Reject, Calibrate</text>
  <text x="1975" y="705" class="card-body">• Resolution appends immutable audit block</text>
  <rect x="1975" y="725" width="320" height="35" rx="8" fill="#fef3c7" />
  <text x="1985" y="747" class="metric-tag" fill="#92400e">TRIAGE: Priority-Based Agronomic Escalation</text>

  <!-- Enterprise RBAC & Security -->
  <rect x="1955" y="820" width="360" height="200" rx="16" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" filter="url(#card-shadow)" />
  <rect x="1975" y="840" width="40" height="40" rx="10" fill="#e0e7ff" stroke="#818cf8" stroke-width="1.5" />
  <text x="1987" y="866" font-size="20">🛡️</text>
  <text x="2030" y="860" class="card-title" fill="#4338ca">Security &amp; Hardened RBAC</text>
  <text x="2030" y="880" class="card-sub">Zero-Trust Access Control</text>
  <text x="1975" y="915" class="card-body">• 4 Roles: Farmer, Agronomist, Auditor, Admin</text>
  <text x="1975" y="935" class="card-body">• Constant-time HMAC comparison (Timing attack safe)</text>
  <text x="1975" y="955" class="card-body">• Path-traversal proof protected static delivery</text>
  <text x="1975" y="975" class="card-body">• CSP &amp; Permissions-Policy security headers</text>

  <!-- Final Delivery & User Interface -->
  <rect x="1955" y="1050" width="360" height="170" rx="16" fill="#f0fdf4" stroke="#86efac" stroke-width="1.5" filter="url(#card-shadow)" />
  <text x="1975" y="1085" class="card-title" fill="#15803d">React 18 + Vite Web Client</text>
  <text x="1975" y="1105" class="card-sub">Role-Based Production Interface</text>
  <text x="1975" y="1135" class="card-body">• Interactive Diagnostics, Grad-CAM slider</text>
  <text x="1975" y="1155" class="card-body">• Traceability verification ledger explorer</text>
  <text x="1975" y="1175" class="card-body">• Agronomist Triage Portal (Resolved / Attention)</text>


  <!-- ========================================================================= -->
  <!-- CONNECTING ARROWS & PIPELINE FLOW PATHS -->
  <!-- ========================================================================= -->
  <!-- Col 1 Specimen -> Pre-flight -->
  <line x1="265" y1="400" x2="265" y2="440" class="arrow" marker-end="url(#arrowhead)" />
  <!-- Col 1 Pre-flight -> Resizing -->
  <line x1="265" y1="660" x2="265" y2="700" class="arrow" marker-end="url(#arrowhead)" />
  <!-- Col 1 Resizing -> Worker -->
  <line x1="265" y1="890" x2="265" y2="930" class="arrow" marker-end="url(#arrowhead)" />

  <!-- Col 1 Resizing -> Col 2 Health Classifier -->
  <path d="M 445 780 C 480 780, 480 355, 545 355" class="arrow-accent" marker-end="url(#arrowhead-emerald)" />
  
  <!-- Col 2 Health Classifier -> Calibration -->
  <line x1="730" y1="470" x2="730" y2="500" class="arrow" marker-end="url(#arrowhead)" />
  <!-- Col 2 Calibration -> Health Gate -->
  <line x1="730" y1="700" x2="730" y2="730" class="arrow" marker-end="url(#arrowhead)" />
  
  <!-- Col 2 Health Gate -> Healthy Exit (Down) -->
  <line x1="730" y1="880" x2="730" y2="910" class="arrow-accent" marker-end="url(#arrowhead-emerald)" />
  <text x="745" y="898" class="branch-text" fill="#059669">Healthy (≥60%)</text>

  <!-- Col 2 Health Gate -> Col 3 Diseased Flow (Right) -->
  <path d="M 915 805 C 955 805, 960 355, 1015 355" stroke="#f43f5e" stroke-width="3" fill="none" stroke-linecap="round" marker-end="url(#arrowhead-rose)" />
  <path d="M 915 805 C 955 805, 960 615, 1015 615" stroke="#f43f5e" stroke-width="3" fill="none" stroke-linecap="round" marker-end="url(#arrowhead-rose)" />
  <text x="925" y="795" class="branch-text" fill="#e11d48">Diseased (&gt;50%)</text>

  <!-- Col 3 Crop + Disease -> Compatibility Gate -->
  <path d="M 1200 470 L 1200 760" class="arrow" marker-end="url(#arrowhead)" />
  <path d="M 1200 730 L 1200 760" class="arrow" marker-end="url(#arrowhead)" />

  <!-- Col 3 Compatibility Gate -> Knowledge Base -->
  <line x1="1200" y1="1010" x2="1200" y2="1040" class="arrow" marker-end="url(#arrowhead)" />

  <!-- Col 1 Resizing Stream B -> Col 4 U-Net (Long bridge) -->
  <path d="M 445 800 C 470 850, 1420 280, 1485 360" stroke="#8b5cf6" stroke-width="2.5" fill="none" stroke-dasharray="6,4" marker-end="url(#arrowhead)" />

  <!-- Col 4 U-Net -> Severity -->
  <line x1="1670" y1="480" x2="1670" y2="510" class="arrow" marker-end="url(#arrowhead)" />
  <!-- Col 3 Disease -> Col 4 Grad-CAM -->
  <path d="M 1385 615 C 1435 615, 1440 885, 1485 885" stroke="#d946ef" stroke-width="2.5" fill="none" marker-end="url(#arrowhead)" />
  
  <!-- Col 4 Severity + Grad-CAM -> Visual Stream -->
  <path d="M 1670 1000 L 1670 1030" class="arrow" marker-end="url(#arrowhead)" />

  <!-- Col 4 Severity / Disease -> Col 5 Blockchain & Review Queue -->
  <path d="M 1855 360 C 1900 360, 1910 360, 1955 360" stroke="#0ea5e9" stroke-width="3" fill="none" marker-end="url(#arrowhead-blue)" />
  <path d="M 1855 625 C 1900 625, 1910 650, 1955 650" stroke="#f59e0b" stroke-width="3" fill="none" marker-end="url(#arrowhead)" />

  <!-- Col 5 Review Queue -> Blockchain -->
  <line x1="2135" y1="530" x2="2135" y2="500" class="arrow" marker-end="url(#arrowhead)" />
  <!-- Col 5 Blockchain -> RBAC/Web Client -->
  <line x1="2135" y1="790" x2="2135" y2="820" class="arrow" marker-end="url(#arrowhead)" />
  <line x1="2135" y1="1020" x2="2135" y2="1050" class="arrow" marker-end="url(#arrowhead)" />

</svg>
"""
    output_path.write_text(svg_content.strip(), encoding="utf-8")
    print(f"[OK] Wrote SVG: {output_path}")

def render_png_from_svg(svg_path: Path, png_path: Path):
    """
    Renders high-resolution publication PNG using Pillow.
    Renders vector geometric boxes, headers, text, metric badges, and arrows.
    """
    width, height = 2400, 1350
    img = Image.new("RGB", (width, height), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)

    # Load high quality fonts
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    font_path = font_paths[0] if os.path.exists(font_paths[0]) else font_paths[1]
    
    font_title = ImageFont.truetype(font_path, 32)
    font_sub = ImageFont.truetype(font_path, 16)
    font_header = ImageFont.truetype(font_path, 15)
    font_card_title = ImageFont.truetype(font_path, 16)
    font_card_sub = ImageFont.truetype(font_path, 13)
    font_body = ImageFont.truetype(font_path, 12)
    font_tag = ImageFont.truetype(font_path, 11)

    # 1. Header Card
    draw.rounded_rectangle([60, 40, 2340, 140], radius=20, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
    draw.ellipse([86, 66, 134, 114], fill=(236, 253, 245), outline=(16, 185, 129), width=2)
    draw.line([(100, 90), (107, 97), (122, 82)], fill=(5, 150, 105), width=3)
    
    draw.text((150, 60), "HARVEST HARBOR: END-TO-END MULTI-TIER SYSTEM ARCHITECTURE", font=font_title, fill=(15, 23, 42))
    draw.text((150, 98), "Interpretable Foliar Pathology Inference, Temperature Calibration, U-Net Lesion Segmentation, SHA-256 Ledger & Agronomist Triage", font=font_sub, fill=(100, 116, 139))
    
    # Status Badge
    draw.rounded_rectangle([2070, 70, 2300, 110], radius=12, fill=(240, 253, 244), outline=(134, 239, 172), width=2)
    draw.ellipse([2089, 84, 2101, 96], fill=(34, 197, 94))
    draw.text((2115, 82), "PRODUCTION VERIFIED", font=font_card_sub, fill=(21, 128, 61))

    # Helper for Column Containers
    cols = [
        (60, 410, "1. INGESTION & PRE-FLIGHT"),
        (520, 420, "2. TIER-1 HEALTH SCREENING"),
        (990, 420, "3. TAXONOMY & PATHOLOGY"),
        (1460, 420, "4. SEGMENTATION & EXPLAINABILITY"),
        (1930, 410, "5. TRUST, AUDIT & TRIAGE"),
    ]

    for x, w, title in cols:
        draw.rounded_rectangle([x, 165, x + w, 1300], radius=24, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
        draw.rounded_rectangle([x, 165, x + w, 215], radius=24, fill=(241, 245, 249))
        draw.rectangle([x, 195, x + w, 215], fill=(241, 245, 249))
        draw.text((x + 25, 180), title, font=font_header, fill=(30, 41, 59))

    # Helper for drawing card
    def draw_card(x, y, w, h, title, sub, bullets, tag_text=None, tag_color=(220, 252, 231), text_color=(2, 132, 199)):
        draw.rounded_rectangle([x, y, x + w, y + h], radius=16, fill=(248, 250, 252), outline=(203, 213, 225), width=2)
        draw.text((x + 20, y + 16), title, font=font_card_title, fill=text_color)
        draw.text((x + 20, y + 36), sub, font=font_card_sub, fill=(71, 85, 105))
        
        by = y + 62
        for b in bullets:
            draw.text((x + 20, by), b, font=font_body, fill=(51, 65, 85))
            by += 18
            
        if tag_text:
            draw.rounded_rectangle([x + 20, y + h - 38, x + w - 20, y + h - 12], radius=6, fill=tag_color)
            draw.text((x + 30, y + h - 33), tag_text, font=font_tag, fill=(15, 23, 42))

    # Column 1 Cards
    draw_card(85, 240, 360, 160, "Foliar Leaf Specimen", "Field Camera / Upload", [
        "• Raw formats: JPEG, PNG, WEBP (Max 15 MB)",
        "• Captured foliar blade under daylight illumination",
        "• Multipart/form-data with Bearer Token"
    ], text_color=(2, 132, 199))

    draw_card(85, 440, 360, 220, "Pre-Flight Quality Guard", "Deterministic Input Validation", [
        "• Magic Byte & MIME validation (Strict check)",
        "• Max decoded pixel cap: 50 MP (DoS Guard)",
        "• Min geometry check: 32x32 px (Blur filter)",
        "• Safe path sanitization & filename hashing"
    ], tag_text="PASS: Stream split to CNN & U-Net formats", tag_color=(254, 249, 195), text_color=(217, 119, 6))

    draw_card(85, 700, 360, 190, "Dual-Stream Resizing", "Color & Tensor Normalization", [
        "• Stream A: 224x224x3 RGB (EfficientNet-B0)",
        "• Stream B: 256x256x3 RGB (U-Net PlantSeg)",
        "• ImageNet Mean/Std Normalization: [0, 1]",
        "• Non-blocking executor dispatch"
    ], text_color=(51, 65, 85))

    draw_card(85, 930, 360, 140, "Async Executor Slots", "FastAPI Concurrency Core", [
        "• Max 4 concurrent ML workers via Semaphore",
        "• Zero event-loop starvation under high RPS",
        "• Per-IP rate limit: 100 req/min"
    ], text_color=(21, 128, 61))

    # Column 2 Cards
    draw_card(545, 240, 370, 230, "Binary Health Classifier", "EfficientNet-B0 Foliar Screening", [
        "• Architecture: EfficientNet-B0 backbone",
        "• Classes: Healthy (C0) vs. Diseased (C1)",
        "• Accuracy: 100.00% (PlantVillage Test Split)",
        "• Precision: 100.00% | Recall: 100.00% | F1: 1.00"
    ], tag_text="EVAL: Acc 100% | Sens 100% | Spec 100%", tag_color=(220, 252, 231), text_color=(5, 150, 105))

    draw_card(545, 500, 370, 200, "Confidence Calibration", "Post-Hoc Temperature Scaling", [
        "• Formulation: p = softmax(z / T), T = 0.05",
        "• Uncalibrated ECE (T=1.0): 2.30%",
        "• Calibrated ECE (T=0.05): 1.00% (56.5% drop)"
    ], tag_text="ECE: 2.30% -> 1.00% (Reliable Probabilities)", tag_color=(219, 234, 254), text_color=(29, 78, 216))

    draw_card(545, 730, 370, 150, "Confidence Gating Logic", "Binary Branch Decision", [
        "• If Healthy & Conf >= 60%: Trigger Healthy Exit",
        "• If Diseased & Conf >= 50%: Advance to Tiers 2-5",
        "• If Uncertain: Escalate to Review Queue"
    ], text_color=(194, 65, 12))

    draw_card(545, 910, 370, 180, "Healthy Branch Exit", "Disease Diagnosis Suppressed", [
        "• Issues Healthy Plant Certificate with SHA-256 seal",
        "• Recommends Good Agricultural Practices (GAP)",
        "• Suppresses false-positive disease protocols",
        "• Records audit proof on immutable blockchain"
    ], text_color=(4, 120, 87))

    # Column 3 Cards
    draw_card(1015, 240, 370, 230, "Crop Species Classifier", "14-Class Botanical EfficientNet-B0", [
        "• 14 Crop Taxa: Apple, Corn, Grape, Potato...",
        "• Top-1 Accuracy: 100.00% (N=140 held-out split)",
        "• Top-3 Accuracy: 100.00% | Zero Cross-Crop Drift",
        "• Provides botanical prior for compatibility gate"
    ], tag_text="EVAL: 14/14 Crops 100% Precision & Recall", tag_color=(220, 252, 231), text_color=(22, 163, 74))

    draw_card(1015, 500, 370, 230, "PlantWild-v2 Classifier", "115-Class Pathology Network", [
        "• 115 Foliar Pathologies & Health Categories",
        "• Deep feature extraction via top_activation layer",
        "• Uncalibrated Top-3 ranked candidate probabilities",
        "• Outputs raw logits vector across 115 classes"
    ], tag_text="OUTPUT: Unfiltered 115-Class Logits Vector", tag_color=(254, 226, 226), text_color=(220, 38, 38))

    draw_card(1015, 760, 370, 250, "Compatibility Gating Filter", "Crop-Aware Masking Matrix", [
        "• Cross-references Predicted Crop x Disease Domain",
        "• Zeroes out cross-family anomalies:",
        "  e.g. Suppresses Apple Scab if leaf is Tomato",
        "• Renormalizes filtered distribution over valid set",
        "• Preserves raw candidate tail for audit transparency"
    ], tag_text="RESULT: Robust Agronomic Top-3 Diagnosis", tag_color=(243, 232, 255), text_color=(126, 34, 206))

    draw_card(1015, 1040, 370, 180, "19-Disease Knowledge Base", "Agronomic Action Plan Generator", [
        "• Curated agronomic markdown profiles",
        "• Cultural controls, chemical timing, bio-fungicides",
        "• Integrated Pest Management (IPM) adherence"
    ], text_color=(15, 23, 42))

    # Column 4 Cards
    draw_card(1485, 240, 370, 240, "U-Net Lesion Segmenter", "Encoder-Decoder with Skip Connections", [
        "• Input Tensor: 256x256x3 RGB (SavedModel)",
        "• Mean IoU (Jaccard Index): 44.30% (PlantSeg N=50)",
        "• Mean Dice Coefficient (F1): 55.52%",
        "• Pixel Precision: 61.33% | Pixel Recall: 65.22%",
        "• Pixel Mask: Background vs Blade vs Lesion"
    ], tag_text="BENCHMARK: Mean IoU 44.30% | Dice 55.52%", tag_color=(237, 233, 254), text_color=(109, 40, 217))

    draw_card(1485, 510, 370, 230, "Severity Tiering Engine", "Quantitative Pixel Ratio Formulation", [
        "• Formulation: Severity = (Σ P_lesion / Σ P_leaf) x 100%",
        "• Mean Absolute Error (MAE): 13.95% foliar area",
        "• Tier Classification Accuracy: 52.00%",
        "• Tiers: Healthy (0%), Early (<15%),",
        "  Moderate (15-35%), Severe (>=35%)"
    ], tag_text="MAE: 13.95% | 4-Tier Categorization", tag_color=(255, 228, 230), text_color=(225, 29, 72))

    draw_card(1485, 770, 370, 230, "Grad-CAM Explainability", "Foliar Attention Attribution", [
        "• Target Layer: top_activation (EfficientNet-B0)",
        "• Gradient of target pathology w.r.t feature maps",
        "• Generates normalized colormap overlay (JET/TURBO)",
        "• Verifies model visual focus on genuine lesions"
    ], tag_text="INTERPRETABILITY: Grounded Heatmap Overlay", tag_color=(250, 232, 255), text_color=(192, 38, 211))

    draw_card(1485, 1030, 370, 190, "Visual Inspection Stream", "Tri-View Diagnostic Presentation", [
        "• View 1: Original High-Resolution Specimen",
        "• View 2: Grad-CAM Saliency Heatmap Overlay",
        "• View 3: U-Net Folium & Lesion Segment Mask",
        "• Interactive opacity & toggle controls"
    ], text_color=(15, 118, 110))

    # Column 5 Cards
    draw_card(1955, 240, 360, 260, "SHA-256 Evidence Ledger", "Tamper-Evident Audit Chain", [
        "• Genesis Block & Canonical Cryptographic Hashes",
        "• H_n = SHA-256(H_{n-1} || Report ID || Metadata)",
        "• File-locking concurrency (zero race conditions)",
        "• Records model weights hash, inputs & decisions",
        "• 100% Cryptographic Verification Endpoint"
    ], tag_text="INTEGRITY: SHA-256 Tamper-Evident Ledger", tag_color=(226, 232, 240), text_color=(15, 23, 42))

    draw_card(1955, 530, 360, 260, "Agronomist Review Queue", "Human-in-the-Loop Clinical Triage", [
        "• Auto-Escalation triggers: High severity (>=35%),",
        "  low confidence, or crop-disease conflict",
        "• Priority Queuing: CRITICAL, HIGH, NORMAL",
        "• Agronomist override: Confirm, Reject, Calibrate",
        "• Resolution appends immutable audit block"
    ], tag_text="TRIAGE: Priority-Based Agronomic Escalation", tag_color=(254, 243, 199), text_color=(180, 83, 9))

    draw_card(1955, 820, 360, 200, "Security & Hardened RBAC", "Zero-Trust Access Control", [
        "• 4 Roles: Farmer, Agronomist, Auditor, Admin",
        "• Constant-time HMAC comparison (Timing attack safe)",
        "• Path-traversal proof protected static delivery",
        "• CSP & Permissions-Policy security headers"
    ], text_color=(67, 56, 202))

    draw_card(1955, 1050, 360, 170, "React 18 + Vite Web Client", "Role-Based Production Interface", [
        "• Interactive Diagnostics, Grad-CAM slider",
        "• Traceability verification ledger explorer",
        "• Agronomist Triage Portal (Resolved / Attention)"
    ], text_color=(21, 128, 61))

    # Connectors & Arrows (Drawn cleanly with lines and arrowheads)
    arrow_color = (148, 163, 184)
    emerald_color = (16, 185, 129)
    rose_color = (244, 63, 94)

    # Col 1 arrows
    draw.line([(265, 400), (265, 440)], fill=arrow_color, width=3)
    draw.line([(265, 660), (265, 700)], fill=arrow_color, width=3)
    draw.line([(265, 890), (265, 930)], fill=arrow_color, width=3)

    # Col 1 -> Col 2
    draw.line([(445, 780), (480, 780), (480, 355), (545, 355)], fill=emerald_color, width=3)

    # Col 2 arrows
    draw.line([(730, 470), (730, 500)], fill=arrow_color, width=3)
    draw.line([(730, 700), (730, 730)], fill=arrow_color, width=3)
    draw.line([(730, 880), (730, 910)], fill=emerald_color, width=3)
    draw.text((745, 885), "Healthy (>=60%)", font=font_card_sub, fill=(5, 150, 105))

    # Col 2 -> Col 3
    draw.line([(915, 805), (960, 805), (960, 355), (1015, 355)], fill=rose_color, width=3)
    draw.line([(960, 615), (1015, 615)], fill=rose_color, width=3)
    draw.text((925, 785), "Diseased (>50%)", font=font_card_sub, fill=(225, 29, 72))

    # Col 3 arrows
    draw.line([(1200, 470), (1200, 760)], fill=arrow_color, width=3)
    draw.line([(1200, 730), (1200, 760)], fill=arrow_color, width=3)
    draw.line([(1200, 1010), (1200, 1040)], fill=arrow_color, width=3)

    # Col 3 -> Col 4
    draw.line([(1385, 615), (1435, 615), (1435, 885), (1485, 885)], fill=(217, 70, 239), width=3)

    # Col 4 arrows
    draw.line([(1670, 480), (1670, 510)], fill=arrow_color, width=3)
    draw.line([(1670, 1000), (1670, 1030)], fill=arrow_color, width=3)

    # Col 4 -> Col 5
    draw.line([(1855, 360), (1955, 360)], fill=(14, 165, 233), width=3)
    draw.line([(1855, 625), (1900, 625), (1900, 650), (1955, 650)], fill=(245, 158, 11), width=3)

    # Col 5 vertical arrows
    draw.line([(2135, 500), (2135, 530)], fill=arrow_color, width=3)
    draw.line([(2135, 790), (2135, 820)], fill=arrow_color, width=3)
    draw.line([(2135, 1020), (2135, 1050)], fill=arrow_color, width=3)

    img.save(png_path, "PNG", dpi=(300, 300))
    print(f"[OK] Wrote High-Res PNG: {png_path} ({png_path.stat().st_size / 1024:.1f} KB)")

def main():
    root = Path(__file__).resolve().parent.parent
    fig_dir = root / "docs" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    targets = [
        ("system_block_diagram.svg", "system_block_diagram.png"),
        ("fig7_system_architecture_pipeline.svg", "fig7_system_architecture_pipeline.png"),
        ("10_system_block_diagram.svg", "10_system_block_diagram.png"),
    ]

    for svg_name, png_name in targets:
        svg_file = fig_dir / svg_name
        png_file = fig_dir / png_name
        generate_svg(svg_file)
        render_png_from_svg(svg_file, png_file)

if __name__ == "__main__":
    main()
