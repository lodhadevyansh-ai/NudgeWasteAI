# NudgeWasteAI — Phase 1: Machine Learning Dataset Discovery and Analysis

**Document Path:** `Machine_Learning/datasets/dataset_analysis.md`  
**Execution Date:** 2026-10-01  
**Target Classification Scope:** 4 Waste Streams:
1. **Wet** (Biodegradable, kitchen organic waste, food scraps, vegetable/fruit peels, garden waste)
2. **Dry** (Recyclable packaging, plastic, paper, cardboard, metal cans, glass bottles, clean dry disposables)
3. **Sanitary** (Menstrual hygiene products, diapers, personal hygiene wipes, cotton pads, bandages)
4. **Special Care** (Hazardous domestic/biomedical waste, e-waste, domestic chemicals, batteries, sharp objects, expired medicines, clinical disposables)

---

## Executive Summary & Dataset Inventory

Six datasets present within `Machine_Learning/datasets/` were comprehensively inspected without modifying any files, moving directories, or altering configurations.

| Dataset Name | Primary Data Modality | Total Files on Disk | Total Images | Image Formats | Annotation Format | Classification Compatibility |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Garbage_Classification** | Images (Single Object) | 2,532 files | 2,527 | JPEG (`.jpg`) | Directory-based + TXT split files | **Directly Compatible** |
| **Garbage_Dataset_(GD)** | Images (Single Object / Pre-scaled) | 30,332 files | 30,332 | JPEG (`.jpg`, `.jpeg`) | Directory-based | **Directly Compatible** (Has redundant resolutions) |
| **Medical_Waste_Dataset** | Multi-Modal Vision (RGB + Stereo Pair) | 5,667 files | 4,245 (1,415 RGB + 2,830 Stereo) | JPEG (`.jpeg`), PNG (`.png`) | Directory + COCO JSON + Pascal VOC XML | **Requires Preprocessing** (Filter stereo PNGs) |
| **TACO** | Contextual Scene Vision (Object Detection / Seg) | 1,822 files | 1,500 real images | JPEG (`.jpg`) | COCO JSON (Polygons & BBoxes) | **Requires Preprocessing** (Requires BBox cropping) |
| **Waste_Classification_Dataset** | Images (Binary Organic / Recyclable) | 50,154 files | 50,154 (25,077 unique) | JPEG (`.jpg`) | Directory-based (TRAIN/TEST splits) | **Directly Compatible** (Has nested clone directory) |
| **india_waste_metrics** | Tabular / Municipal Statistics | 2 CSV files | 0 | None (Tabular) | CSV tabular schemas | **Not a Vision Dataset** (Contextual / Nudge Analytics only) |

---

## 1. Dataset: Garbage_Classification

### 1.1 Overview & Directory Structure
- **Path:** `Machine_Learning/datasets/Garbage_Classification/`
- **Total Size on Disk:** ~41.39 MB
- **Directory Structure:**
  ```text
  Garbage_Classification/
  ├── Garbage classification/
  │   └── Garbage classification/
  │       ├── cardboard/          [403 images]
  │       ├── glass/              [501 images]
  │       ├── metal/              [410 images]
  │       ├── paper/              [594 images]
  │       ├── plastic/            [482 images]
  │       └── trash/              [137 images]
  ├── one-indexed-files-notrash_test.txt     [431 lines]
  ├── one-indexed-files-notrash_train.txt    [1,768 lines]
  ├── one-indexed-files-notrash_val.txt      [328 lines]
  ├── one-indexed-files.txt                  [2,527 lines]
  └── zero-indexed-files.txt                 [2,527 lines]
  ```

### 1.2 Image File Formats & Quantities
- **Image Count:** 2,527 images
- **Image Format:** 100% JPEG (`.jpg`), 3-channel RGB
- **Image Resolution:** Uniform 512 x 384 pixels
- **Category Counts:**
  - `cardboard`: 403
  - `glass`: 501
  - `metal`: 410
  - `paper`: 594
  - `plastic`: 482
  - `trash`: 137

### 1.3 Existing Labels & Annotation Format
- **Labels:** 6 classes (`cardboard`, `glass`, `metal`, `paper`, `plastic`, `trash`)
- **Annotation Format:**
  - Folder-based classification (subfolder name = class label).
  - Explicit index mapping files:
    - `zero-indexed-files.txt`: Maps filenames to indices `0..5` (`0: glass`, `1: paper`, `2: cardboard`, `3: plastic`, `4: metal`, `5: trash`).
    - `one-indexed-files.txt`: Maps filenames to indices `1..6`.
    - Split lists (`one-indexed-files-notrash_*.txt`): Pre-defined train (1,768), validation (328), and test (431) splits that purposefully exclude the ambiguous `trash` category.

### 1.4 Potential Usefulness
- Clean, curated, single-object images captured on white background under uniform studio lighting.
- High-quality training data for standard recyclable dry materials (`cardboard`, `glass`, `metal`, `paper`, `plastic`).

### 1.5 Required Preprocessing
- Address path nesting (`Garbage classification/Garbage classification/`).
- Standardize image normalization (mean/std) and resize to target model input size (e.g., 224 x 224).

### 1.6 Potential Problems
- **Background bias:** Studio white background does not represent messy real-world household sorting environments.
- **Class imbalance:** `trash` has only 137 samples, and its semantic definition is vague (miscellaneous mixed items).
- Completely lacks **Wet** (organic) and **Sanitary** samples.

### 1.7 Suitability for Final 4-Class Classifier
- **Suitable for:** **Dry** class (specifically `cardboard`, `glass`, `metal`, `paper`, `plastic`).
- **Not suitable for:** Cannot represent **Wet**, **Sanitary**, or **Special Care**. The `trash` subset requires inspection or omission due to ambiguity.

---

## 2. Dataset: Garbage_Dataset_(GD)

### 2.1 Overview & Directory Structure
- **Path:** `Machine_Learning/datasets/Garbage_Dataset_(GD)/`
- **Total Size on Disk:** ~928.59 MB
- **Directory Structure:**
  ```text
  Garbage_Dataset_(GD)/
  ├── original/                     [5,814 images across 6 classes]
  │   ├── glass/                    [49 images]
  │   ├── metal/                    [930 images]
  │   ├── paper/                    [1,336 images]
  │   ├── plastic/                  [1,597 images]
  │   ├── shoes/                    [1,449 images]
  │   └── trash/                    [453 images]
  ├── standardized_256/             [12,259 images across 10 classes, 256x256]
  │   ├── battery/                  [756 images]
  │   ├── biological/               [699 images]
  │   ├── cardboard/                [1,411 images]
  │   ├── clothes/                  [1,892 images]
  │   ├── glass/                    [1,736 images]
  │   ├── metal/                    [930 images]
  │   ├── paper/                    [1,336 images]
  │   ├── plastic/                  [1,597 images]
  │   ├── shoes/                    [1,449 images]
  │   └── trash/                    [453 images]
  └── standardized_384/             [12,259 images across 10 classes, 384x384]
      └── [Exact duplicate structure and image counts as standardized_256]
  ```

### 2.2 Image File Formats & Quantities
- **Total Files:** 30,332 images (.jpg: 30,329, .jpeg: 3)
- **Unique Samples:** 12,259 unique images (duplicated between `standardized_256` and `standardized_384`, with `original` holding 5,814 raw resolution counterparts).
- **Subdirectory Resolutions:**
  - `original`: Variable aspect ratios (e.g. ~225 x 225).
  - `standardized_256`: Center-cropped / padded square 256 x 256 pixels.
  - `standardized_384`: Center-cropped / padded square 384 x 384 pixels.
- **Category Counts (in standardized sets):**
  - `battery`: 756
  - `biological`: 699
  - `cardboard`: 1,411
  - `clothes`: 1,892
  - `glass`: 1,736
  - `metal`: 930
  - `paper`: 1,336
  - `plastic`: 1,597
  - `shoes`: 1,449
  - `trash`: 453

### 2.3 Existing Labels & Annotation Format
- **Labels:** 10 distinct classes in standardized folders (`battery`, `biological`, `cardboard`, `clothes`, `glass`, `metal`, `paper`, `plastic`, `shoes`, `trash`).
- **Annotation Format:** Standard directory-based classification hierarchy.

### 2.4 Potential Usefulness
- Highly valuable: One of the few vision datasets in this repository containing explicit categories for **Wet** (`biological`: 699 images) and **Special Care** (`battery`: 756 images).
- Includes substantial dry categories (`cardboard`, `glass`, `metal`, `paper`, `plastic`) plus dry non-recyclable / reusable goods (`clothes`, `shoes`).

### 2.5 Required Preprocessing
- **De-duplication / Resolution selection:** Do NOT train simultaneously on `standardized_256` and `standardized_384`. One standardized resolution (or `original` plus standardized extras) must be selected during data loading.
- Stratified train/val/test split generation.

### 2.6 Potential Problems
- `original/glass` has only 49 images, whereas `standardized_*/glass` has 1,736 images (standardized folders combined external sources).
- `clothes` and `shoes` require domain clarity (typically dry non-recyclables or donation stream).

### 2.7 Suitability for Final 4-Class Classifier
- **Highly Suitable:**
  - `biological` is a direct candidate for **Wet**.
  - `cardboard`, `glass`, `metal`, `paper`, `plastic` are direct candidates for **Dry**.
  - `battery` is a prime candidate for domestic hazardous e-waste in **Special Care**.
  - Does NOT contain explicit **Sanitary** items.

---

## 3. Dataset: Medical_Waste_Dataset

### 3.1 Overview & Directory Structure
- **Path:** `Machine_Learning/datasets/Medical_Waste_Dataset/`
- **Total Size on Disk:** ~803.67 MB
- **Dataset Identification:** Medical Waste 4.0 Annotated Dataset (Tuscany Region project, Luxonis OAK-D sensor).
- **Directory Structure:**
  ```text
  Medical_Waste_Dataset/
  └── Medical Waste dataset/
      ├── dataset-metadata.json
      ├── annotations/
      │   ├── coco/
      │   │   ├── summary.json          [total_xml: 1415, train: 990, val: 212, test: 213]
      │   │   ├── train.json            [990 images, 990 annotations, 13 categories]
      │   │   ├── val.json              [212 images, 212 annotations, 13 categories]
      │   │   ├── test.json             [213 images, 213 annotations, 13 categories]
      │   │   └── train_smoke.json
      │   └── xml/                      [1,415 Pascal VOC XML files]
      └── images/
          ├── readme.txt
          ├── gauze/                    [393 files: 131 RGB + 262 stereo PNGs]
          ├── glove_pair_latex/         [330 files: 110 RGB + 220 stereo PNGs]
          ├── glove_pair_nitrile/       [330 files: 110 RGB + 220 stereo PNGs]
          ├── glove_pair_surgery/       [300 files: 100 RGB + 200 stereo PNGs]
          ├── glove_single_latex/       [303 files: 101 RGB + 202 stereo PNGs]
          ├── glove_single_nitrile/     [333 files: 111 RGB + 222 stereo PNGs]
          ├── glove_single_surgery/     [306 files: 102 RGB + 204 stereo PNGs]
          ├── medical_cap/              [306 files: 102 RGB + 204 stereo PNGs]
          ├── medical_glasses/          [318 files: 106 RGB + 212 stereo PNGs]
          ├── shoe_cover_pair/          [351 files: 117 RGB + 234 stereo PNGs]
          ├── shoe_cover_single/        [312 files: 104 RGB + 208 stereo PNGs]
          ├── test_tube/                [363 files: 121 RGB + 242 stereo PNGs]
          └── urine_bag/                [300 files: 100 RGB + 200 stereo PNGs]
  ```

### 3.2 Image File Formats & Quantities
- **Total Image Files:** 4,245 files.
- **Physical Samples:** Exactly 1,415 distinct capture instances.
- **Sensor Triplet Structure:** Each physical capture contains 3 image files:
  1. RGB Image: `<timestamp>.jpeg` (1920 x 1080, 3-channel RGB) — 1,415 files.
  2. Stereo Left: `<timestamp>_l.png` (640 x 400, 1-channel Grayscale) — 1,415 files.
  3. Stereo Right: `<timestamp>_r.png` (640 x 400, 1-channel Grayscale) — 1,415 files.
- **Category Counts (Physical RGB Samples):**
  - `gauze`: 131
  - `glove_pair_latex`: 110
  - `glove_pair_nitrile`: 110
  - `glove_pair_surgery`: 100
  - `glove_single_latex`: 101
  - `glove_single_nitrile`: 111
  - `glove_single_surgery`: 102
  - `medical_cap`: 102
  - `medical_glasses`: 106
  - `shoe_cover_pair`: 117
  - `shoe_cover_single`: 104
  - `test_tube`: 121
  - `urine_bag`: 100

### 3.3 Existing Labels & Annotation Format
- **Labels (13 classes):** `gauze`, `glove pair latex`, `glove pair nitrile`, `glove pair surgery`, `glove single latex`, `glove single nitrile`, `glove single surgery`, `medical cap`, `medical glasses`, `shoe cover pair`, `shoe cover single`, `test tube`, `urine bag`.
- **Annotation Formats:**
  - Dual format: Full COCO JSON (`annotations/coco/`) and Pascal VOC XML (`annotations/xml/`).
  - Pre-split COCO files: `train.json` (990), `val.json` (212), `test.json` (213).

### 3.4 Potential Usefulness
- Critical and rare dataset for bio-medical, clinical, and personal protective equipment waste.
- High visual quality (1080p RGB) with precise bounding box coordinates and classification labels.

### 3.5 Required Preprocessing
- **Stereo Filtering:** The 2,830 grayscale stereo PNG files (`*_l.png`, `*_r.png`) MUST be filtered out if training a 3-channel RGB image classifier, or else single-channel images will cause channel shape mismatch errors or severe distortion.
- **Resolution Downsampling:** 1920 x 1080 RGB images need resizing/scaling to standard ML input sizes.

### 3.6 Potential Problems
- Lab / conveyor environment with clinical backgrounds.
- High class granularity (6 sub-variations of gloves, 2 variations of shoe covers) that need aggregation.

### 3.7 Suitability for Final 4-Class Classifier
- **High Suitability:**
  - Essential data source for **Special Care** (hazardous biomedical waste: `test_tube`, `urine_bag`, clinical gloves).
  - Can also potentially support **Sanitary** (e.g. `gauze`, disposable biological protective covers), subject to segregation definitions.

---

## 4. Dataset: TACO (Trash Annotations in Context)

### 4.1 Overview & Directory Structure
- **Path:** `Machine_Learning/datasets/TACO/`
- **Total Size on Disk:** ~2,619.65 MB (~2.56 GB)
- **Directory Structure:**
  ```text
  TACO/
  ├── __MACOSX/                     [Redundant macOS resource fork metadata]
  └── TACO/
      ├── .git/                     [Git repository metadata]
      ├── data/
      │   ├── annotations.json      [Consolidated COCO annotation file]
      │   ├── batch_1/ .. batch_15/ [1,500 images across 15 batch folders]
      │   └── [Individual batch annotations.json in each folder]
      └── detector/
          ├── taco_config/
          │   ├── map_2.csv, map_3.csv, map_4.csv, map_17.csv
          │   └── background_imgs   [List of remote image URLs]
          ├── dataset.py, model.py, detector.py
          └── [Mask R-CNN detector code]
  ```

### 4.2 Image File Formats & Quantities
- **Total Genuine Images:** Exactly 1,500 JPEG images in `TACO/TACO/data/` across 15 batches (`batch_1` through `batch_15`).
- **Image Format:** High-resolution RGB JPEG (`.jpg`).
- **Resolutions:** High resolution, non-uniform (e.g., 1537 x 2049, 4000 x 3000, 2448 x 3264).
- *Note:* 14 files in `__MACOSX/` prefixed with `._` are macOS AppleDouble metadata headers, not actual images.

### 4.3 Existing Labels & Annotation Format
- **Annotation Format:** Standard COCO Object Detection / Instance Segmentation JSON (`annotations.json`).
  - Total Annotated Images: 1,500
  - Total Annotations: 4,784 segmentation polygons and bounding boxes (`bbox: [x, y, w, h]`).
  - Categories: 60 fine-grained categories organized under 28 supercategories.
  - Categories include: `Aluminium foil`, `Battery`, `Aluminium blister pack`, `Carded blister pack`, `Clear plastic bottle`, `Glass bottle`, `Plastic bottle cap`, `Metal bottle cap`, `Broken glass`, `Food Can`, `Aerosol`, `Drink can`, `Toilet tube`, `Corrugated carton`, `Egg carton`, `Pizza box`, `Paper cup`, `Disposable plastic cup`, `Food waste`, `Glass jar`, `Plastic lid`, `Magazine paper`, `Tissues`, `Paper bag`, `Plastic film`, `Crisp packet`, `Disposable food container`, `Plastic glooves`, `Cigarette`, etc.
  - Pre-existing mapping configurations exist in `taco_config/` (`map_17.csv`, `map_4.csv`, `map_3.csv`, `map_2.csv`).

### 4.4 Potential Usefulness
- Highly realistic "in the wild" litter imagery captured in natural, urban, and household scenes with complex real-world backgrounds.
- Rich variety of objects representing both Dry recyclables, food waste, packaging, and hazardous items like batteries and blister packs.

### 4.5 Required Preprocessing
- **Object Extraction / Bounding Box Cropping Required:** TACO is an **object detection** dataset, not a single-label image classification dataset. A single image typically contains 3 to 10 distinct litter items of different categories against complex ground/street backgrounds.
- To utilize TACO for an image classifier, individual objects must be cropped out using the annotated bounding boxes (`bbox`) from `annotations.json`.
- Ignore OS artifacts (`__MACOSX/`, `.git/`).

### 4.6 Potential Problems
- Direct full-image classification cannot be performed without cropping, as images have multiple competing labels.
- Extreme aspect ratios and varying object sizes (from tiny cigarette butts to large cardboard boxes).

### 4.7 Suitability for Final 4-Class Classifier
- **Conditionally Suitable (Requires Bounding Box Cropping):**
  - Once cropped via bounding boxes, crops provide valuable samples for:
    - **Dry:** plastic bottles, cans, cartons, lids, wrappers.
    - **Wet:** `Food waste` annotations.
    - **Special Care:** `Battery`, `Aerosol`.
    - **Sanitary:** `Tissues`, `Plastic glooves`.

---

## 5. Dataset: Waste_Classification_Dataset

### 5.1 Overview & Directory Structure
- **Path:** `Machine_Learning/datasets/Waste_Classification_Dataset/`
- **Total Size on Disk:** ~423.88 MB
- **Directory Structure:**
  ```text
  Waste_Classification_Dataset/
  └── DATASET/
      ├── TEST/
      │   ├── O/                    [1,401 images]
      │   └── R/                    [1,112 images]
      ├── TRAIN/
      │   ├── O/                    [12,565 images]
      │   └── R/                    [9,999 images]
      └── DATASET/                  [IDENTICAL NESTED DUPLICATE]
          ├── TEST/
          │   ├── O/                [1,401 images]
          │   └── R/                [1,112 images]
          └── TRAIN/
              ├── O/                [12,565 images]
              └── R/                [9,999 images]
  ```

### 5.2 Image File Formats & Quantities
- **Total Files on Disk:** 50,154 image files (`.jpg`).
- **Unique Samples:** 25,077 unique images.
- **Redundancy Analysis:** The subdirectory `DATASET/DATASET/` contains a byte-for-byte, name-for-name identical duplicate copy of the outer `DATASET/TEST/` and `DATASET/TRAIN/` trees (25,077 duplicates).
- **Split & Label Distribution (Unique Images):**
  - **TRAIN Set:** 22,564 images
    - `O` (Organic): 12,565 images (`O_1.jpg` to `O_12567.jpg`)
    - `R` (Recyclable): 9,999 images (`R_1.jpg` to `R_9999.jpg`)
  - **TEST Set:** 2,513 images
    - `O` (Organic): 1,401 images (`O_12568.jpg` to `O_13968.jpg`)
    - `R` (Recyclable): 1,112 images (`R_10000.jpg` to `R_11111.jpg`)
  - **Total O:** 13,966 images
  - **Total R:** 11,111 images

### 5.3 Existing Labels & Annotation Format
- **Labels:** 2 binary categories:
  - `O`: Organic waste (vegetables, fruits, food remains, organic kitchen waste, leaves).
  - `R`: Recyclable waste (plastic containers, glass, cans, paper, cardboard).
- **Annotation Format:** Standard subfolder directory structure (`TRAIN/O`, `TRAIN/R`, `TEST/O`, `TEST/R`).

### 5.4 Potential Usefulness
- Provides massive visual volume (25,077 unique samples).
- Highly potent source for **Wet** (`O` class with ~14k samples) and **Dry** (`R` class with ~11k samples).
- Pre-separated official train and test partitions.

### 5.5 Required Preprocessing
- **Bypass Redundant Clone:** Data loaders must explicitly target `DATASET/TRAIN` and `DATASET/TEST` while ignoring `DATASET/DATASET/` to prevent duplicate loading and data leakage.
- Normalization and standard resizing (images are varied around 200–300 pixels).

### 5.6 Potential Problems
- Low image resolution in certain web-scraped images.
- Coarse binary split does not separate paper vs plastic vs metal, nor does it provide Sanitary or Special Care.

### 5.7 Suitability for Final 4-Class Classifier
- **Highly Suitable:**
  - `O` is the single largest and strongest training source for **Wet**.
  - `R` is a major volume contributor for **Dry**.
  - Does NOT contribute to **Sanitary** or **Special Care**.

---

## 6. Dataset: india_waste_metrics

### 6.1 Overview & Directory Structure
- **Path:** `Machine_Learning/datasets/india_waste_metrics/`
- **Total Size on Disk:** ~0.23 MB (232 KB)
- **Directory Structure:**
  ```text
  india_waste_metrics/
  ├── Waste_Management_and_Recycling_India_cleaned.csv     [850 rows, 13 columns]
  └── Waste_Management_with_Extra_Features.csv             [850 rows, 18 columns]
  ```

### 6.2 Data Type, Structure & Quantities
- **Vision Modality:** Contains **ZERO** images.
- **Data Modality:** Purely tabular / relational municipal waste data.
- **Dataset Contents:**
  - `Waste_Management_and_Recycling_India_cleaned.csv`:
    - Rows: 850 municipal records across Indian cities/districts (e.g. Mumbai, Delhi, Bengaluru, etc.).
    - Columns (13): `city/district`, `waste_type`, `waste_generated_(tons/day)`, `recycling_rate_(%)`, `population_density_(people/km²)`, `municipal_efficiency_score_(1_10)`, `disposal_method`, `cost_of_waste_management_(₹/ton)`, `awareness_campaigns_count`, `landfill_name`, `landfill_location_(lat,_long)`, `landfill_capacity_(tons)`, `year`.
  - `Waste_Management_with_Extra_Features.csv`:
    - Rows: 850 records.
    - Columns (18): Includes all 13 columns above plus 5 engineered sustainability features:
      - `waste_reduction_initiatives`
      - `industrial_symbiosis_index`
      - `community_participation_score`
      - `green_technology_adoption`
      - `recycling_infrastructure_rating`

### 6.3 Existing Labels & Annotation Format
- Tabular CSV format with UTF-8 encoding (contains Indian Rupee symbol `₹`).

### 6.4 Potential Usefulness
- **Non-Vision ML / Backend Nudge Engine:** Not useful for computer vision image classification.
- **High Utility for NudgeWasteAI Platform:**
  - Contextual behavioral nudges (e.g. "Segregating this dry recyclable helps save ~₹3,000/ton in municipal processing costs").
  - City-level recycling impact calculations, municipal leaderboard analytics, and carbon offset estimations.

### 6.5 Required Preprocessing
- For tabular models/analytics: Standard tabular feature engineering, encoding categorical fields (`city/district`, `waste_type`, `disposal_method`), standard scaling of numerical indicators.

### 6.6 Potential Problems
- Not applicable to computer vision image classification.

### 6.7 Suitability for Final 4-Class Classifier
- **Not Suitable for Image Classification:** Cannot be used to train the 4-class computer vision model because it contains no imagery.

---

## 7. Comparative Synthesis & Architectural Suitability

### 7.1 Cross-Dataset Redundancy & Duplications Identified
1. **Waste_Classification_Dataset Internal Clone:**
   - `DATASET/DATASET/` is an exact clone of `DATASET/TRAIN` and `DATASET/TEST`.
   - Action for Phase 2/3: Configure data loader roots to read only `DATASET/TRAIN` and `DATASET/TEST`, avoiding the nested `DATASET/DATASET/` path.
2. **Garbage_Dataset_(GD) Resolution Duplication:**
   - `standardized_256` (12,259 images) and `standardized_384` (12,259 images) contain identical samples at two pre-scaled resolutions.
   - Action for Phase 2/3: Select a single resolution root to avoid doubling training time with duplicate data.
3. **Medical Waste Stereo Grayscale Pairs:**
   - 2,830 of the 4,245 files in `Medical_Waste_Dataset` are stereo auxiliary PNGs (`*_l.png`, `*_r.png`).
   - Action for Phase 2/3: Filter dataset ingestion strictly to RGB files (`*.jpeg`), isolating the 1,415 primary samples.
4. **TACO OS & Git Artifacts:**
   - `__MACOSX/` and `.git/` contain non-data system files.

### 7.2 Classification Compatibility Matrix

| Dataset | Modality | Direct Classifier Compatibility | Reason |
| :--- | :--- | :--- | :--- |
| **Garbage_Classification** | Single-label images | **High** | Uniform images, standard directory structure. |
| **Garbage_Dataset_(GD)** | Single-label images | **High** | Standard directory structure, pre-standardized dimensions. |
| **Medical_Waste_Dataset** | Single-label images + Stereo | **Medium (Requires filter)** | Images sorted by class, but stereo grayscale PNGs must be excluded. |
| **TACO** | Multi-object scene images | **Low (Requires BBox crop)** | Multi-object scenes with bounding boxes; requires cropping pipeline. |
| **Waste_Classification_Dataset** | Single-label images | **High** | Pre-partitioned TRAIN/TEST directory structure. |
| **india_waste_metrics** | Tabular records | **None (Vision)** | Tabular metrics dataset; no images present. |

### 7.3 Candidate Stream Alignment for Target Classes

| Target Application Class | Candidate Contributing Datasets & Subsets |
| :--- | :--- |
| **Wet** | `Waste_Classification_Dataset` (`TRAIN/O`, `TEST/O`: 13,966 samples)<br>`Garbage_Dataset_(GD)` (`biological`: 699 samples)<br>`TACO` (Cropped `Food waste` annotations) |
| **Dry** | `Waste_Classification_Dataset` (`TRAIN/R`, `TEST/R`: 11,111 samples)<br>`Garbage_Classification` (`cardboard`, `glass`, `metal`, `paper`, `plastic`: 2,390 samples)<br>`Garbage_Dataset_(GD)` (`cardboard`, `glass`, `metal`, `paper`, `plastic`: ~7,010 samples)<br>`TACO` (Cropped packaging, bottles, cans, paper) |
| **Sanitary** | `Medical_Waste_Dataset` (`gauze`, `medical_cap`, `shoe_cover_*`: ~450 RGB samples)<br>`TACO` (Cropped `Tissues`, `Plastic glooves`) |
| **Special Care** | `Garbage_Dataset_(GD)` (`battery`: 756 samples)<br>`Medical_Waste_Dataset` (`test_tube`, `urine_bag`, clinical gloves: ~965 RGB samples)<br>`TACO` (Cropped `Battery`, `Aerosol`) |

*(Note: In accordance with Phase 1 safety rules, the formal class mapping definition is deferred to subsequent phases.)*

---

## Conclusion & Status

All six datasets have been thoroughly investigated, empirically measured, and documented in place without modifying any source files.

**FINAL STATUS:**
**DATASET ANALYSIS COMPLETE**
