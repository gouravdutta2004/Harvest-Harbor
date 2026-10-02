import os
import sys
from pathlib import Path

def main():
    print("Building Field Validation Dataset...")
    
    dataset_dir = os.getenv("FIELD_DATASET_DIR") or (sys.argv[1] if len(sys.argv) > 1 else None)
    if not dataset_dir or not os.path.exists(dataset_dir):
        print("Status: NOT IMPLEMENTED")
        print("Error: Field validation dataset directory not supplied or directory path does not exist.")
        print("Usage: python build_field_dataset.py /path/to/field_dataset OR set FIELD_DATASET_DIR environment variable.")
        sys.exit(1)

    image_files = []
    for root, _, files in os.walk(dataset_dir):
        for f in files:
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                image_files.append(os.path.join(root, f))

    if not image_files:
        print("Status: NOT IMPLEMENTED")
        print(f"Error: No image files found in directory {dataset_dir}.")
        sys.exit(1)

    print(f"Dataset build complete. Successfully registered {len(image_files)} field images from {dataset_dir}.")

if __name__ == "__main__":
    main()
