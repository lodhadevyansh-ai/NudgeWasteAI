# NudgeWasteAI — Processed Datasets Directory

This directory stores generated manifests, metadata, and cached preprocessing outputs for the NudgeWasteAI four-class classifier:
1. **Wet**
2. **Dry**
3. **Sanitary**
4. **Special Care**

## Structure

```text
Machine_Learning/datasets/processed/
├── README.md                          <- This document
└── manifests/
    └── dataset_manifest.csv            <- Master index of all 40,805 verified samples across 5 datasets
```

## Zero-Duplication Architecture

In accordance with Phase 3 guidelines (Task 12: *Avoid unnecessary image duplication*), the image data is **not** cloned or duplicated onto disk. Instead:
- Raw images remain in their original source directories.
- The `dataset_manifest.csv` references original paths, bounding boxes, original labels, and canonical class mappings.
- The `preprocessing/dataset_loader.py` module reads images directly from source, applying deterministic validation, format handling, aspect-ratio-preserving resizing, and ImageNet normalization on the fly during training and evaluation.

## Manifest Schema

| Column | Description |
| :--- | :--- |
| `image_path` | Absolute filesystem path to the original image file |
| `dataset_name` | Source dataset name (e.g., `Garbage_Classification`, `TACO`) |
| `original_label` | Original label from source dataset |
| `canonical_class` | Target class (`Wet`, `Dry`, `Sanitary`, `Special Care`) |
| `canonical_idx` | Target integer index (`0`, `1`, `2`, `3`) |
| `bbox_x`, `bbox_y`, `bbox_w`, `bbox_h` | Optional bounding box coordinates for object crops (e.g., TACO) |
| `split` | Original dataset split if pre-defined (`train`, `test`) |
