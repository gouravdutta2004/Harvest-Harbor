"""
Harvest Harbor — Research Paper Evaluation Figures Generator
============================================================
Generates publication-grade evaluation charts and confusion matrices
corresponding to the empirical tables in docs/RESEARCH_EVALUATION.md:
  - fig1_crop_confusion_matrix (14x14)
  - fig2_severity_confusion_matrix (4x4)
  - fig3_health_confusion_matrix (2x2)
  - fig4_segmentation_performance (IoU, Dice, Precision, Recall)
  - fig5_calibration_reliability_diagram (Uncalibrated vs Calibrated ECE)
  - fig6_disease_per_class_f1 (F1-score per evaluated disease)
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def get_fonts():
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    font_path = font_paths[0] if os.path.exists(font_paths[0]) else font_paths[1]
    return {
        "title": ImageFont.truetype(font_path, 22),
        "header": ImageFont.truetype(font_path, 15),
        "cell": ImageFont.truetype(font_path, 13),
        "label": ImageFont.truetype(font_path, 12),
        "small": ImageFont.truetype(font_path, 10),
    }

def generate_crop_confusion_matrix(fig_dir: Path):
    """Figure 1: 14x14 Crop Confusion Matrix (100% Top-1 accuracy across 14 crops)."""
    crops = [
        'Apple', 'Blueberry', 'Cherry', 'Corn', 'Grape', 'Orange', 'Peach',
        'Pepper', 'Potato', 'Raspberry', 'Soybean', 'Squash', 'Strawberry', 'Tomato'
    ]
    N = len(crops)
    w, h = 1200, 1050
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()

    # Title
    draw.text((80, 40), "FIGURE 1: Dedicated Crop Classifier Confusion Matrix (14 × 14)", font=fonts["title"], fill=(15, 23, 42))
    draw.text((80, 75), "Held-out test split (N=140, 10 samples per class). Diagonal entries = 10, Off-diagonal = 0 (100.00% Top-1 Accuracy).", font=fonts["header"], fill=(100, 116, 139))

    # Grid offsets
    start_x, start_y = 220, 140
    cell_w, cell_h = 55, 55

    # Draw axis labels
    for j, crop in enumerate(crops):
        cx = start_x + j * cell_w + cell_w // 2
        # Abbreviate or rotate angle
        abbr = crop[:4] if len(crop) > 5 else crop
        draw.text((cx - 15, start_y - 25), abbr, font=fonts["small"], fill=(51, 65, 85))

    for i, crop in enumerate(crops):
        cy = start_y + i * cell_h + cell_h // 2
        draw.text((start_x - 140, cy - 8), crop, font=fonts["label"], fill=(15, 23, 42))

        for j in range(N):
            x0 = start_x + j * cell_w
            y0 = start_y + i * cell_h
            x1 = x0 + cell_w
            y1 = y0 + cell_h

            if i == j:
                # Diagonal = 10
                fill_color = (16, 185, 129) # Emerald green
                text_color = (255, 255, 255)
                val_str = "10"
            else:
                fill_color = (248, 250, 252) # Very light slate
                text_color = (148, 163, 184)
                val_str = "0"

            draw.rectangle([x0, y0, x1, y1], fill=fill_color, outline=(226, 232, 240), width=1)
            draw.text((x0 + cell_w // 2 - 8, y0 + cell_h // 2 - 8), val_str, font=fonts["cell"], fill=text_color)

    # Colorbar / Legend
    legend_y = start_y + N * cell_h + 40
    draw.rectangle([start_x, legend_y, start_x + 30, legend_y + 20], fill=(16, 185, 129))
    draw.text((start_x + 40, legend_y + 3), "Correct Classifications (n = 10)", font=fonts["label"], fill=(15, 23, 42))

    draw.rectangle([start_x + 280, legend_y, start_x + 310, legend_y + 20], fill=(248, 250, 252), outline=(226, 232, 240))
    draw.text((start_x + 320, legend_y + 3), "Zero Misclassifications (n = 0)", font=fonts["label"], fill=(100, 116, 139))

    png_path = fig_dir / "fig1_crop_confusion_matrix.png"
    img.save(png_path, "PNG", dpi=(300, 300))
    print(f"[OK] Wrote: {png_path}")

def generate_severity_confusion_matrix(fig_dir: Path):
    """Figure 2: 4x4 Foliar Severity Tier Confusion Matrix."""
    tiers = ['Healthy (0%)', 'Early (<15%)', 'Moderate (15-35%)', 'Severe (>=35%)']
    # Matrix data from RESEARCH_EVALUATION.md
    matrix = [
        [0,  3, 1, 2],
        [0, 13, 8, 1],
        [0,  4, 4, 2],
        [1,  1, 1, 9],
    ]
    w, h = 950, 800
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()

    draw.text((80, 40), "FIGURE 2: Foliar Severity Tier Confusion Matrix (4 × 4)", font=fonts["title"], fill=(15, 23, 42))
    draw.text((80, 75), "U-Net lesion segmentation vs PlantSeg ground truth (N=50). Accuracy = 52.00%, MAE = 13.95% foliar area.", font=fonts["header"], fill=(100, 116, 139))

    start_x, start_y = 260, 150
    cell_w, cell_h = 130, 90

    # Predicted Headers (Top)
    draw.text((start_x + 160, start_y - 45), "PREDICTED SEVERITY TIER", font=fonts["header"], fill=(15, 23, 42))
    for j, tier in enumerate(tiers):
        draw.text((start_x + j * cell_w + 10, start_y - 20), tier, font=fonts["small"], fill=(71, 85, 105))

    # Ground Truth Headers (Left)
    for i, tier in enumerate(tiers):
        draw.text((start_x - 170, start_y + i * cell_h + cell_h // 2 - 8), tier, font=fonts["label"], fill=(15, 23, 42))

        for j in range(4):
            x0 = start_x + j * cell_w
            y0 = start_y + i * cell_h
            x1 = x0 + cell_w
            y1 = y0 + cell_h
            val = matrix[i][j]

            # Heatmap interpolation
            if val == 0:
                fill_color = (248, 250, 252)
                text_color = (148, 163, 184)
            elif i == j:
                # Diagonal
                fill_color = (5, 150, 105) if val > 5 else (52, 211, 153)
                text_color = (255, 255, 255)
            else:
                # Off-diagonal error
                fill_color = (254, 226, 226) if val > 3 else (254, 242, 242)
                text_color = (185, 28, 28)

            draw.rectangle([x0, y0, x1, y1], fill=fill_color, outline=(226, 232, 240), width=1)
            draw.text((x0 + cell_w // 2 - 8, y0 + cell_h // 2 - 8), str(val), font=fonts["title"], fill=text_color)

    png_path = fig_dir / "fig2_severity_confusion_matrix.png"
    img.save(png_path, "PNG", dpi=(300, 300))
    print(f"[OK] Wrote: {png_path}")

def generate_health_confusion_matrix(fig_dir: Path):
    """Figure 3: 2x2 Binary Health Screening Confusion Matrix."""
    matrix = [
        [25, 0],
        [0, 25]
    ]
    w, h = 850, 650
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()

    draw.text((80, 40), "FIGURE 3: Binary Health Screening Confusion Matrix (2 × 2)", font=fonts["title"], fill=(15, 23, 42))
    draw.text((80, 75), "EfficientNet-B0 (Healthy vs Diseased) on PlantVillage test set (N=50). Accuracy = 100.00%.", font=fonts["header"], fill=(100, 116, 139))

    start_x, start_y = 260, 150
    cell_w, cell_h = 180, 130

    labels = ["Healthy (C0)", "Diseased (C1)"]
    for j, lab in enumerate(labels):
        draw.text((start_x + j * cell_w + 35, start_y - 25), lab, font=fonts["header"], fill=(15, 23, 42))
    for i, lab in enumerate(labels):
        draw.text((start_x - 140, start_y + i * cell_h + cell_h // 2 - 8), lab, font=fonts["header"], fill=(15, 23, 42))

        for j in range(2):
            x0 = start_x + j * cell_w
            y0 = start_y + i * cell_h
            val = matrix[i][j]
            fill_color = (16, 185, 129) if i == j else (248, 250, 252)
            text_color = (255, 255, 255) if i == j else (148, 163, 184)

            draw.rectangle([x0, y0, x0 + cell_w, y0 + cell_h], fill=fill_color, outline=(226, 232, 240), width=1)
            draw.text((x0 + cell_w // 2 - 12, y0 + cell_h // 2 - 12), str(val), font=fonts["title"], fill=text_color)

    png_path = fig_dir / "fig3_health_confusion_matrix.png"
    img.save(png_path, "PNG", dpi=(300, 300))
    print(f"[OK] Wrote: {png_path}")

def generate_segmentation_benchmark(fig_dir: Path):
    """Figure 4: U-Net Lesion Segmentation Benchmark Metrics Bar Chart."""
    metrics = [
        ("Pixel Recall", 65.22, (59, 130, 246)),
        ("Pixel Precision", 61.33, (16, 185, 129)),
        ("Mean Dice (F1)", 55.52, (139, 92, 246)),
        ("Mean IoU (Jaccard)", 44.30, (236, 72, 153)),
    ]
    w, h = 900, 600
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()

    draw.text((80, 40), "FIGURE 4: U-Net Lesion Segmentation Benchmark (PlantSeg N=50)", font=fonts["title"], fill=(15, 23, 42))
    draw.text((80, 75), "Pixel-level evaluation against human-annotated foliar lesion ground truth masks.", font=fonts["header"], fill=(100, 116, 139))

    start_x, start_y = 220, 140
    bar_h = 50
    spacing = 80
    max_w = 500

    for i, (name, val, color) in enumerate(metrics):
        y = start_y + i * spacing
        draw.text((60, y + 14), name, font=fonts["header"], fill=(15, 23, 42))

        # Bar background
        draw.rounded_rectangle([start_x, y, start_x + max_w, y + bar_h], radius=8, fill=(241, 245, 249))
        # Active bar
        bw = int((val / 100.0) * max_w)
        draw.rounded_rectangle([start_x, y, start_x + bw, y + bar_h], radius=8, fill=color)

        # Value label
        draw.text((start_x + bw + 15, y + 14), f"{val:.2f}%", font=fonts["header"], fill=color)

    png_path = fig_dir / "fig4_segmentation_performance.png"
    img.save(png_path, "PNG", dpi=(300, 300))
    print(f"[OK] Wrote: {png_path}")

def generate_calibration_chart(fig_dir: Path):
    """Figure 5: Post-Hoc Probability Calibration Error (ECE) Comparison."""
    w, h = 850, 550
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()

    draw.text((80, 40), "FIGURE 5: Expected Calibration Error (ECE) Reduction", font=fonts["title"], fill=(15, 23, 42))
    draw.text((80, 75), "Temperature Scaling (T=0.05) vs Uncalibrated Raw Softmax (T=1.0). 56.5% error reduction.", font=fonts["header"], fill=(100, 116, 139))

    bars = [
        ("Uncalibrated (T = 1.0)", 2.30, (239, 68, 68)), # Rose red
        ("Calibrated (T = 0.05)", 1.00, (16, 185, 129)), # Emerald green
    ]

    start_x, start_y = 280, 160
    bar_h = 60
    spacing = 100
    max_w = 400

    for i, (name, val, color) in enumerate(bars):
        y = start_y + i * spacing
        draw.text((50, y + 18), name, font=fonts["header"], fill=(15, 23, 42))

        draw.rounded_rectangle([start_x, y, start_x + max_w, y + bar_h], radius=8, fill=(241, 245, 249))
        bw = int((val / 3.0) * max_w) # scale out of 3%
        draw.rounded_rectangle([start_x, y, start_x + bw, y + bar_h], radius=8, fill=color)
        draw.text((start_x + bw + 15, y + 18), f"ECE = {val:.2f}%", font=fonts["header"], fill=color)

    png_path = fig_dir / "fig5_calibration_reliability_diagram.png"
    img.save(png_path, "PNG", dpi=(300, 300))
    print(f"[OK] Wrote: {png_path}")

def generate_disease_f1_chart(fig_dir: Path):
    """Figure 6: Per-Class F1-Scores on Evaluated Foliar Pathologies."""
    diseases = [
        ("Apple Black Rot", 60.00, (245, 158, 11)),
        ("Tomato Leaf Mold", 66.67, (16, 185, 129)),
        ("Corn Gray Leaf Spot", 54.55, (59, 130, 246)),
        ("Grape Black Rot", 50.00, (139, 92, 246)),
        ("Bell Pepper Bacterial Spot", 40.00, (236, 72, 153)),
        ("Strawberry Leaf Scorch", 40.00, (239, 68, 68)),
    ]
    w, h = 950, 700
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()

    draw.text((80, 40), "FIGURE 6: Foliar Pathology F1-Scores (PlantWild Benchmark)", font=fonts["title"], fill=(15, 23, 42))
    draw.text((80, 75), "Empirical test performance across evaluated leaf disease categories.", font=fonts["header"], fill=(100, 116, 139))

    start_x, start_y = 280, 140
    bar_h = 42
    spacing = 70
    max_w = 480

    for i, (name, val, color) in enumerate(diseases):
        y = start_y + i * spacing
        draw.text((50, y + 12), name, font=fonts["label"], fill=(15, 23, 42))

        draw.rounded_rectangle([start_x, y, start_x + max_w, y + bar_h], radius=8, fill=(241, 245, 249))
        bw = int((val / 100.0) * max_w)
        draw.rounded_rectangle([start_x, y, start_x + bw, y + bar_h], radius=8, fill=color)
        draw.text((start_x + bw + 15, y + 12), f"F1: {val:.2f}%", font=fonts["header"], fill=color)

    png_path = fig_dir / "fig6_disease_per_class_f1.png"
    img.save(png_path, "PNG", dpi=(300, 300))
    print(f"[OK] Wrote: {png_path}")

def main():
    root = Path(__file__).resolve().parent.parent
    fig_dir = root / "docs" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    generate_crop_confusion_matrix(fig_dir)
    generate_severity_confusion_matrix(fig_dir)
    generate_health_confusion_matrix(fig_dir)
    generate_segmentation_benchmark(fig_dir)
    generate_calibration_chart(fig_dir)
    generate_disease_f1_chart(fig_dir)

if __name__ == "__main__":
    main()
