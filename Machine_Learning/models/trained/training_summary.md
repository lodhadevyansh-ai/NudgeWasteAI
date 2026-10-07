# NudgeWasteAI — Phase 6 Model Training Report

- **Execution Date:** 2026-10-06 23:47:58
- **Model Architecture:** `mobilenet_v3_small`
- **Target Classes:** `Wet, Dry, Sanitary, Special Care`
- **Training Epochs:** 5
- **Batch Size:** 32
- **Learning Rate:** 0.001
- **Optimizer:** AdamW
- **Best Validation Macro F1:** **0.9165** (Epoch 5)
- **Best Model Path:** `C:\Users\lodha\Downloads\NudgeWasteAI\Machine_Learning\models\trained\nudgewaste_mobilenetv3_small_best.pt`

## Training History

| Epoch | Stage | Train Loss | Train Acc | Val Loss | Val Acc | Val Macro F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Stage 1: Frozen Backbone | 0.6177 | 75.36% | 0.4516 | 80.55% | **0.8084** |
| 2 | Stage 2: Full Fine-Tuning | 0.3375 | 87.43% | 0.4728 | 83.59% | **0.8318** |
| 3 | Stage 2: Full Fine-Tuning | 0.1675 | 94.36% | 0.3148 | 88.75% | **0.8887** |
| 4 | Stage 2: Full Fine-Tuning | 0.0805 | 97.64% | 0.2491 | 91.19% | **0.9148** |
| 5 | Stage 2: Full Fine-Tuning | 0.0621 | 98.29% | 0.2186 | 91.49% | **0.9165** |


## Best Epoch Per-Class Performance

| Canonical Class | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| **Wet** | 91.11% | 93.18% | 0.9213 | 88 |
| **Dry** | 86.21% | 85.23% | 0.8571 | 88 |
| **Sanitary** | 92.54% | 95.38% | 0.9394 | 65 |
| **Special Care** | 96.47% | 93.18% | 0.9480 | 88 |

> [!NOTE]
> Production readiness cannot be determined from training metrics alone. Comprehensive out-of-sample evaluation on the official test split will be conducted in Phase 7.
