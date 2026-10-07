# NudgeWasteAI — Machine Learning Core Component

This folder contains the complete end-to-end Machine Learning pipeline for **NudgeWasteAI**, an automated waste classification system categorizing items into four canonical categories: **Wet**, **Dry**, **Sanitary**, and **Special Care**.

---

## 1. Project Overview & Target Classes

| Class Index | Canonical Class | Description / Target Waste Types |
| :---: | :--- | :--- |
| `0` | **Wet** | Organic food scraps, kitchen waste, compostables, wet yard waste |
| `1` | **Dry** | Paper, cardboard, plastics, metals, glass, dry recyclable packaging |
| `2` | **Sanitary** | Used personal hygiene items, diapers, wipes, medical masks/gloves |
| `3` | **Special Care** | E-waste, batteries, chemicals, hazardous materials, light bulbs |

---

## 2. Model Architecture & Metrics

* **Architecture:** MobileNetV3-Small (`mobilenet_v3_small`) with transfer learning from ImageNet pre-trained weights and a custom 4-output classification head.
* **Input Resolution:** `224 x 224` pixels (3 RGB channels).
* **Dataset Size:** 40,786 valid, non-corrupt multi-dataset images (32,512 Train / 3,988 Val / 4,286 Test).
* **Test Metrics:**
  * **Test Accuracy:** `87.12%`
  * **Macro F1-Score:** `0.7540`

---

## 3. Production Deployment & Inference Specifications

### 3.1 Final Model Formats
Trained weights and optimized deployment graphs are stored under [`models/trained/`](file:///c:/Users/lodha/Downloads/NudgeWasteAI/Machine_Learning/models/trained/):
1. **PyTorch State Checkpoint:** [`nudgewaste_mobilenetv3_small_best.pt`](file:///c:/Users/lodha/Downloads/NudgeWasteAI/Machine_Learning/models/trained/nudgewaste_mobilenetv3_small_best.pt) (17.67 MB)
   - Contains PyTorch `state_dict`, architecture parameters, class mapping, and training metadata.
2. **TorchScript Traced Model:** [`nudgewaste_mobilenetv3_small.torchscript.pt`](file:///c:/Users/lodha/Downloads/NudgeWasteAI/Machine_Learning/models/trained/nudgewaste_mobilenetv3_small.torchscript.pt) (6.23 MB)
   - Optimized graph compiled for mobile/edge runtimes (PyTorch Mobile Android/iOS, C++ LibTorch runtime) without Python runtime requirements. (~65% memory footprint reduction).

### 3.2 Expected Input Dimensions
* **Tensor Shape:** `(Batch, 3, 224, 224)` float tensor.
* **Batch Size:** `1` (single image inference) or arbitrary batch size.

### 3.3 Expected Preprocessing Steps
All input images must be processed identically to training:
1. **Format Handling:** Convert input image to RGB. If RGBA, apply white background alpha compositing.
2. **Letterbox Resizing:** Resize image to fit within `224 x 224` preserving original aspect ratio, with black padding added symmetrically (`(0, 0, 0)`).
3. **Normalization:** Convert pixel values to `[0.0, 1.0]` float and apply ImageNet normalization:
   * **Mean:** `[0.485, 0.456, 0.406]`
   * **Std:** `[0.229, 0.224, 0.225]`

### 3.4 Inference API Usage

#### Programmatic Usage in Python:
```python
from inference.predictor import predict_image, get_predictor

# Quick single image inference
result = predict_image("path/to/waste_sample.jpg")

print(result)
# Output:
# {
#   "status": "SUCCESS",
#   "predicted_class": "Dry",
#   "confidence": 0.9421,
#   "canonical_idx": 1,
#   "probabilities": {
#     "Wet": 0.0211,
#     "Dry": 0.9421,
#     "Sanitary": 0.0031,
#     "Special Care": 0.0337
#   },
#   "error": None
# }

# Reusable predictor instance (loads weights ONCE into memory)
predictor = get_predictor()
res = predictor.predict(image_bytes_or_pil_image)
```

#### CLI Command Line Usage:
```bash
python inference/predictor.py --image path/to/waste.jpg
```

#### Exporting / Re-compiling TorchScript Graph:
```bash
python inference/export.py --checkpoint models/trained/nudgewaste_mobilenetv3_small_best.pt
```

### 3.5 Runtime Environment Requirements
* **Python:** 3.9+
* **Framework:** PyTorch (`torch >= 2.0.0`), `torchvision`
* **Dependencies:** `Pillow`, `numpy`
* **Hardware:** Runs on CPU (approx. 1.5ms - 3.5ms per prediction) or CUDA GPU.

---

## 4. Code Base Structure

```
Machine_Learning/
├── configs/
│   └── config.py               # Centralized configuration & hyperparameter constants
├── datasets/
│   ├── class_mapping.md        # Comprehensive 6-dataset label mapping rules
│   ├── dataset_analysis.md     # Initial dataset discovery findings
│   └── processed/
│       └── manifests/          # Consolidated 40,786 image dataset manifest (CSV)
├── evaluation/
│   ├── evaluate.py             # Evaluation pipeline on held-out test split
│   ├── evaluation_metrics.json # Full numerical metrics & per-class precision/recall
│   └── evaluation_report.md    # Markdown test evaluation report
├── inference/
│   ├── export.py               # TorchScript model exporter & graph validator
│   └── predictor.py            # Production single-load inference engine
├── models/
│   ├── model.py                # NudgeWasteClassifier (MobileNetV3-Small architecture)
│   └── trained/                # Saved checkpoints & TorchScript models
├── preprocessing/
│   ├── class_mapper.py         # Label mapping translation utility
│   ├── dataset_loader.py       # Custom PyTorch Dataset with letterboxing
│   └── preprocessing.py        # Image validation, letterboxing & normalization
├── training/
│   └── train.py                # Modular PyTorch training engine with validation monitoring
└── tests/                      # Automated unit test suite (42 tests passing)
```

---

## 5. Dataset Manifest & Leakage-Safe Splitting

### 5.1 Manifest Specifications
* **Location:** [`datasets/processed/manifests/dataset_manifest.csv`](file:///c:/Users/lodha/Downloads/NudgeWasteAI/Machine_Learning/datasets/processed/manifests/dataset_manifest.csv)
* **Total Records:** 40,786 samples across 5 vision datasets.
* **Fields:** `image_path`, `dataset_name`, `original_label`, `canonical_class`, `canonical_idx`, `bbox_x`, `bbox_y`, `bbox_w`, `bbox_h`, `split`

### 5.2 Dataset Partitioning & Leakage Prevention Strategy
1. **Garbage_Classification:** Preserves official benchmark split tags (`train`, `val`, `test`).
2. **Garbage_Dataset_(GD):** Applies deterministic class-stratified splitting (80% train, 10% val, 10% test, seed=42).
3. **Medical_Waste_Dataset:** Preserves official COCO partition files (`train.json`, `val.json`, `test.json`) for RGB images.
4. **Waste_Classification_Dataset:** Preserves official benchmark `TEST` split 100% intact, and splits `TRAIN` into train (90%) and val (10%) via class-stratified sampling.
5. **TACO (Group Splitting):** All bounding box crops derived from the same original source image/scene are assigned strictly to a **single** split (`train`, `val`, or `test`). This guarantees **ZERO** multi-crop data leakage between splits.
6. **india_waste_metrics:** Non-vision tabular dataset safely excluded from image classification ingestion.

### 5.3 Canonical Class Distribution Across Splits
All four canonical classes are fully represented in every split:
* **Train (32,512):** Wet: 11,690 | Dry: 19,089 | Sanitary: 396 | Special Care: 1,337
* **Val (3,988):** Wet: 1,477 | Dry: 2,382 | Sanitary: 51 | Special Care: 78
* **Test (4,286):** Wet: 1,506 | Dry: 2,377 | Sanitary: 53 | Special Care: 350

### 5.4 Manifest Generation & Verification Commands

#### Generate Manifest Programmatically:
```python
from preprocessing.dataset_loader import DatasetScanner, DatasetManifest

scanner = DatasetScanner()
samples = scanner.scan_all(seed=42)
manifest = DatasetManifest(samples)
manifest.export_to_csv("datasets/processed/manifests/dataset_manifest.csv")
```

#### Run Full Test & Leakage Verification Suite:
```bash
python -m pytest Machine_Learning/tests -v -rs
python -m compileall Machine_Learning
python -m pip check
```

