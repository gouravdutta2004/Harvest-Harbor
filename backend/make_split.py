import json
import random
from pathlib import Path

ds_dir = Path("../datasets/plantvillage")
val_files = []
val_labels = []

for p in ds_dir.rglob("*.jpg"):
    if "healthy" in p.name.lower() or "healthy" in p.parent.name.lower():
        label = 0
    else:
        label = 1
    val_files.append(str(p.resolve()))
    val_labels.append(label)

# Pick 100 random files
indices = list(range(len(val_files)))
random.shuffle(indices)
indices = indices[:100]

out = {
    "val_files": [val_files[i] for i in indices],
    "val_labels": [val_labels[i] for i in indices]
}
out_dir = Path("health_model")
out_dir.mkdir(exist_ok=True)
(out_dir / "dataset_split.json").write_text(json.dumps(out))
print("Done")
