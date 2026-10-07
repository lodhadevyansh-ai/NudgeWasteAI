# NudgeWasteAI — Phase 7 Model Evaluation Report

- **Evaluated At:** 2026-10-06T23:50:17.905881
- **Model Checkpoint:** `nudgewaste_mobilenetv3_small_best.pt`
- **Architecture:** `mobilenet_v3_small`
- **Inference Device:** `cpu`
- **Held-Out Test Samples:** **4,286**

## 1. Overall Performance Metrics

| Metric | Value |
| :--- | :--- |
| **Overall Accuracy** | **88.47%** |
| **Macro F1-Score** | **0.7977** |
| **Macro Precision** | 73.38% |
| **Macro Recall** | 91.59% |
| **Weighted F1-Score** | 0.8888 |

## 2. Per-Class Performance Breakdown

| Canonical Class | Precision | Recall | F1-Score | Test Support |
| :--- | :--- | :--- | :--- | :--- |
| **Wet** | 86.05% | 95.92% | 0.9072 | 1,472 |
| **Dry** | 97.15% | 83.55% | 0.8984 | 2,529 |
| **Sanitary** | 50.32% | 92.86% | 0.6527 | 84 |
| **Special Care** | 60.00% | 94.03% | 0.7326 | 201 |

## 3. Confusion Matrix

Rows represent True Labels; Columns represent Model Predictions.

| True \ Pred | Wet | Dry | Sanitary | Special Care |
| :--- | :---: | :---: | :---: | :---: |
| **Wet** | 1,412 | 48 | 7 | 5 |
| **Dry** | 228 | 2,113 | 69 | 119 |
| **Sanitary** | 0 | 4 | 78 | 2 |
| **Special Care** | 1 | 10 | 1 | 189 |

## 4. Commonly Confused Classes

| True Class | Predicted As | Misclassified Samples | Error Rate in True Class |
| :--- | :--- | :---: | :---: |
| **Dry** | Wet | 228 | 9.02% |
| **Dry** | Special Care | 119 | 4.71% |
| **Dry** | Sanitary | 69 | 2.73% |
| **Wet** | Dry | 48 | 3.26% |
| **Special Care** | Dry | 10 | 4.98% |

## 5. Inference Speed & Edge Performance

- **Average Latency:** **5.54 ms** per image
- **95th Percentile (P95) Latency:** **7.73 ms**
- **Throughput:** **180.4 FPS** on CPU

## 6. Weaknesses & Inference Readiness Assessment

- Generalization on out-of-distribution real-world household cluttered backgrounds requires continued validation.

### Inference Testing Readiness:
**READY FOR INFERENCE TESTING** — Model demonstrates consistent four-class separation and sub-20ms edge latency. Proceed to Phase 8 inference pipeline integration.
