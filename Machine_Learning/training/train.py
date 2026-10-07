"""
NudgeWasteAI Model Training Pipeline
====================================

Trains the four-class waste classification model (Wet, Dry, Sanitary, Special Care)
using transfer learning on MobileNetV3-Small (or configurable architecture).

Key Features:
-------------
- Transfer Learning: Progressive 2-stage training (frozen backbone warm-up followed
  by full fine-tuning).
- Imbalance-Aware Loss: CrossEntropyLoss with smoothed inverse class weights.
- Metric Tracking: Accuracy, Macro F1, Per-Class Precision/Recall, and Loss.
- Overfitting Detection: Monitors generalization gap and validation loss trends.
- Model Checkpointing: Saves the best model checkpoint based on Validation Macro F1.
- Complete Artifact Logging: Saves model weights (.pt), configuration (.json),
  training history (.json), and human-readable training summary (.md).
"""

import argparse
from datetime import datetime
import json
import logging
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
# Ensure Machine_Learning root is on sys.path for direct script execution
_ml_root = str(Path(__file__).resolve().parent.parent)
if _ml_root not in sys.path:
    sys.path.insert(0, _ml_root)

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support

import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader

from configs.config import (
    CANONICAL_CLASSES,
    CLASS_TO_IDX,
    IDX_TO_CLASS,
    NUM_CLASSES,
    DataConfig,
    ModelConfig,
    TrainingConfig,
    default_data_config,
    default_model_config,
    default_training_config,
)
from models.model import NudgeWasteClassifier, build_model
from preprocessing.dataset_loader import DatasetManifest, get_dataloaders

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def compute_evaluation_metrics(
    y_true: List[int],
    y_pred: List[int],
) -> Dict[str, Any]:
    """
    Compute comprehensive classification metrics across all 4 canonical classes.
    """
    y_t = np.array(y_true)
    y_p = np.array(y_pred)

    overall_acc = float(accuracy_score(y_t, y_p))
    macro_f1 = float(f1_score(y_t, y_p, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_t, y_p, average="weighted", zero_division=0))

    precision_raw, recall_raw, f1_raw, support_raw = precision_recall_fscore_support(
        y_t, y_p, labels=list(range(NUM_CLASSES)), zero_division=0
    )
    precision = np.asarray(precision_raw)
    recall = np.asarray(recall_raw)
    f1 = np.asarray(f1_raw)
    support = np.asarray(support_raw)

    per_class = {}
    for idx, name in IDX_TO_CLASS.items():
        per_class[name] = {
            "precision": float(precision[idx]),
            "recall": float(recall[idx]),
            "f1": float(f1[idx]),
            "support": int(support[idx]),
        }

    return {
        "accuracy": overall_acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "per_class": per_class,
    }


class NudgeWasteTrainer:
    """
    Orchestrates the training lifecycle for NudgeWasteAI.
    """

    def __init__(
        self,
        data_config: Optional[DataConfig] = None,
        model_config: Optional[ModelConfig] = None,
        training_config: Optional[TrainingConfig] = None,
    ):
        self.data_cfg = data_config or default_data_config
        self.model_cfg = model_config or default_model_config
        self.train_cfg = training_config or default_training_config

        # Device selection (CPU or CUDA)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using compute device: {self.device}")

        # Set seeds for deterministic training
        self._set_seed(self.train_cfg.seed)

        logger.info("Initializing DataLoaders with WeightedRandomSampler for class balance...")
        loaders_dict = get_dataloaders(
            config=self.data_cfg,
            batch_size=self.train_cfg.batch_size,
            seed=self.train_cfg.seed,
            max_samples_per_class=self.train_cfg.max_samples_per_class,
            use_weighted_sampler=True,
        )
        self.train_loader: DataLoader = loaders_dict["train_loader"]
        self.val_loader: DataLoader = loaders_dict["val_loader"]
        self.test_loader: DataLoader = loaders_dict["test_loader"]
        self.class_weights: np.ndarray = loaders_dict["class_weights"]
        self.split_dist: Dict = loaders_dict["class_distribution"]

        logger.info(f"Loaded samples -> Train: {len(self.train_loader.dataset):,}, "
                    f"Val: {len(self.val_loader.dataset):,}, Test: {len(self.test_loader.dataset):,}")
        logger.info(f"Class weights: {self.class_weights.tolist()}")

        # Build model
        logger.info(f"Building model: {self.model_cfg.architecture} (pretrained={self.model_cfg.pretrained})...")
        self.model: NudgeWasteClassifier = build_model(
            config=self.model_cfg,
            architecture=self.model_cfg.architecture,
            num_classes=self.model_cfg.num_classes,
            pretrained=self.model_cfg.pretrained,
            dropout_rate=self.model_cfg.dropout_rate,
        ).to(self.device)

        # Loss criterion
        if self.train_cfg.use_class_weights:
            weights_tensor = torch.tensor(self.class_weights, dtype=torch.float32).to(self.device)
            self.criterion = nn.CrossEntropyLoss(weight=weights_tensor)
        else:
            self.criterion = nn.CrossEntropyLoss()

        # Optimizer and Scheduler
        self.optimizer = AdamW(
            self.model.parameters(),
            lr=self.train_cfg.learning_rate,
            weight_decay=self.train_cfg.weight_decay,
        )
        self.scheduler = CosineAnnealingLR(
            self.optimizer,
            T_max=self.train_cfg.epochs,
            eta_min=1e-6,
        )

        # Ensure output directory exists
        self.save_dir = Path(self.train_cfg.save_dir).resolve()
        self.save_dir.mkdir(parents=True, exist_ok=True)

        self.history: List[Dict[str, Any]] = []
        self.best_val_macro_f1 = -1.0
        self.best_epoch = -1

    def _set_seed(self, seed: int) -> None:
        torch.manual_seed(seed)
        np.random.seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

    def train_epoch(self, epoch: int) -> Dict[str, float]:
        """Run training for a single epoch."""
        self.model.train()
        total_loss = 0.0
        all_preds = []
        all_targets = []

        start_time = time.time()
        for batch_idx, (images, targets) in enumerate(self.train_loader):
            images = images.to(self.device)
            targets = targets.to(self.device)

            self.optimizer.zero_grad()
            logits = self.model(images)
            loss = self.criterion(logits, targets)

            loss.backward()
            self.optimizer.step()

            total_loss += loss.item() * images.size(0)
            preds = torch.argmax(logits, dim=-1)
            all_preds.extend(preds.cpu().tolist())
            all_targets.extend(targets.cpu().tolist())

        epoch_time = time.time() - start_time
        avg_loss = total_loss / max(1, len(all_targets))
        train_acc = accuracy_score(all_targets, all_preds)
        train_macro_f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)

        return {
            "loss": float(avg_loss),
            "accuracy": float(train_acc),
            "macro_f1": float(train_macro_f1),
            "time_seconds": float(epoch_time),
        }

    def validate_epoch(self) -> Tuple[float, Dict[str, Any]]:
        """Evaluate model on the validation set."""
        self.model.eval()
        total_loss = 0.0
        all_preds = []
        all_targets = []

        with torch.no_grad():
            for images, targets in self.val_loader:
                images = images.to(self.device)
                targets = targets.to(self.device)

                logits = self.model(images)
                loss = self.criterion(logits, targets)

                total_loss += loss.item() * images.size(0)
                preds = torch.argmax(logits, dim=-1)
                all_preds.extend(preds.cpu().tolist())
                all_targets.extend(targets.cpu().tolist())

        avg_loss = total_loss / max(1, len(all_targets))
        metrics = compute_evaluation_metrics(all_targets, all_preds)
        metrics["loss"] = float(avg_loss)

        return avg_loss, metrics

    def train(self) -> Dict[str, Any]:
        """
        Execute full training loop with progressive transfer learning.
        """
        logger.info("=" * 70)
        logger.info("STARTING NUDGEWASTEAI FOUR-CLASS MODEL TRAINING")
        logger.info(f"Architecture: {self.model_cfg.architecture}")
        logger.info(f"Epochs: {self.train_cfg.epochs} | Batch Size: {self.train_cfg.batch_size} | LR: {self.train_cfg.learning_rate}")
        logger.info(f"Validation Selection Criterion: Best Validation Macro F1")
        logger.info("=" * 70)

        val_metrics: Dict[str, Any] = {}
        for epoch in range(1, self.train_cfg.epochs + 1):
            # Progressive unfreezing: Freeze backbone in early epochs
            if epoch <= self.train_cfg.freeze_backbone_epochs:
                self.model.freeze_backbone()
                stage_str = "Stage 1: Frozen Backbone"
            else:
                self.model.unfreeze_backbone()
                stage_str = "Stage 2: Full Fine-Tuning"

            train_metrics = self.train_epoch(epoch)
            val_loss, val_metrics = self.validate_epoch()
            self.scheduler.step()

            # Overfitting detection
            gen_gap = train_metrics["accuracy"] - val_metrics["accuracy"]
            overfit_alert = False
            if gen_gap > 0.15:
                overfit_alert = True
                logger.warning(f"Overfitting alert: Generalization gap is {gen_gap:.2%} (Train: {train_metrics['accuracy']:.2%}, Val: {val_metrics['accuracy']:.2%})")

            epoch_record = {
                "epoch": epoch,
                "stage": stage_str,
                "train_loss": train_metrics["loss"],
                "train_accuracy": train_metrics["accuracy"],
                "train_macro_f1": train_metrics["macro_f1"],
                "val_loss": val_loss,
                "val_accuracy": val_metrics["accuracy"],
                "val_macro_f1": val_metrics["macro_f1"],
                "generalization_gap": float(gen_gap),
                "overfitting_alert": overfit_alert,
                "learning_rate": float(self.scheduler.get_last_lr()[0]),
                "time_seconds": train_metrics["time_seconds"],
                "val_per_class": val_metrics["per_class"],
            }
            self.history.append(epoch_record)

            logger.info(
                f"Epoch [{epoch:02d}/{self.train_cfg.epochs:02d}] ({stage_str}) | "
                f"Train Loss: {train_metrics['loss']:.4f} | Train Acc: {train_metrics['accuracy']:.2%} | "
                f"Val Loss: {val_loss:.4f} | Val Acc: {val_metrics['accuracy']:.2%} | "
                f"Val Macro F1: {val_metrics['macro_f1']:.4f} "
                f"[{train_metrics['time_seconds']:.1f}s]"
            )

            # Checkpoint: Save best model based on validation macro F1
            if val_metrics["macro_f1"] > self.best_val_macro_f1:
                self.best_val_macro_f1 = val_metrics["macro_f1"]
                self.best_epoch = epoch
                self._save_checkpoint(
                    filename=self.train_cfg.model_filename,
                    epoch=epoch,
                    val_metrics=val_metrics,
                    is_best=True,
                )
                logger.info(f"  -> Saved new best model checkpoint! (Val Macro F1: {self.best_val_macro_f1:.4f})")

        # Save final checkpoint
        self._save_checkpoint(
            filename="nudgewaste_mobilenetv3_small_latest.pt",
            epoch=self.train_cfg.epochs,
            val_metrics=val_metrics,
            is_best=False,
        )

        # Save artifacts
        self._save_artifacts()

        logger.info("=" * 70)
        logger.info(f"TRAINING COMPLETE. Best Epoch: {self.best_epoch} with Val Macro F1: {self.best_val_macro_f1:.4f}")
        logger.info(f"Model saved to: {self.save_dir / self.train_cfg.model_filename}")
        logger.info("=" * 70)

        return {
            "best_epoch": self.best_epoch,
            "best_val_macro_f1": self.best_val_macro_f1,
            "best_model_path": str(self.save_dir / self.train_cfg.model_filename),
            "history": self.history,
        }

    def _save_checkpoint(
        self,
        filename: str,
        epoch: int,
        val_metrics: Dict[str, Any],
        is_best: bool = False,
    ) -> None:
        """Save a comprehensive PyTorch model checkpoint."""
        checkpoint_path = self.save_dir / filename
        checkpoint_data = {
            "epoch": epoch,
            "architecture": self.model_cfg.architecture,
            "num_classes": self.model_cfg.num_classes,
            "canonical_classes": CANONICAL_CLASSES,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "class_weights": self.class_weights.tolist(),
            "val_metrics": val_metrics,
            "is_best": is_best,
            "created_at": datetime.now().isoformat(),
        }
        torch.save(checkpoint_data, checkpoint_path)

    def _save_artifacts(self) -> None:
        """Save training configuration, history JSON, and markdown summary."""
        # 1. Configuration JSON
        config_path = self.save_dir / self.train_cfg.config_filename
        cfg_dict = {
            "model_architecture": self.model_cfg.architecture,
            "num_classes": self.model_cfg.num_classes,
            "canonical_classes": CANONICAL_CLASSES,
            "class_to_idx": CLASS_TO_IDX,
            "pretrained": self.model_cfg.pretrained,
            "epochs": self.train_cfg.epochs,
            "batch_size": self.train_cfg.batch_size,
            "learning_rate": self.train_cfg.learning_rate,
            "optimizer": self.train_cfg.optimizer_name,
            "image_size": list(self.data_cfg.image_size),
            "mean": list(self.data_cfg.mean),
            "std": list(self.data_cfg.std),
            "best_validation_criterion": "Validation Macro F1",
            "best_epoch": self.best_epoch,
            "best_val_macro_f1": self.best_val_macro_f1,
            "final_model_path": str(self.save_dir / self.train_cfg.model_filename),
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(cfg_dict, f, indent=2)

        # 2. History JSON
        metrics_path = self.save_dir / self.train_cfg.metrics_filename
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)

        # 3. Markdown Training Summary
        summary_path = self.save_dir / "training_summary.md"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("# NudgeWasteAI — Phase 6 Model Training Report\n\n")
            f.write(f"- **Execution Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"- **Model Architecture:** `{self.model_cfg.architecture}`\n")
            f.write(f"- **Target Classes:** `{', '.join(CANONICAL_CLASSES)}`\n")
            f.write(f"- **Training Epochs:** {self.train_cfg.epochs}\n")
            f.write(f"- **Batch Size:** {self.train_cfg.batch_size}\n")
            f.write(f"- **Learning Rate:** {self.train_cfg.learning_rate}\n")
            f.write(f"- **Optimizer:** {self.train_cfg.optimizer_name}\n")
            f.write(f"- **Best Validation Macro F1:** **{self.best_val_macro_f1:.4f}** (Epoch {self.best_epoch})\n")
            f.write(f"- **Best Model Path:** `{self.save_dir / self.train_cfg.model_filename}`\n\n")

            f.write("## Training History\n\n")
            f.write("| Epoch | Stage | Train Loss | Train Acc | Val Loss | Val Acc | Val Macro F1 |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
            for h in self.history:
                f.write(f"| {h['epoch']} | {h['stage']} | {h['train_loss']:.4f} | {h['train_accuracy']:.2%} | {h['val_loss']:.4f} | {h['val_accuracy']:.2%} | **{h['val_macro_f1']:.4f}** |\n")

            f.write("\n\n## Best Epoch Per-Class Performance\n\n")
            best_record = self.history[self.best_epoch - 1] if self.best_epoch > 0 else self.history[-1]
            f.write("| Canonical Class | Precision | Recall | F1-Score | Support |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")
            for c_name in CANONICAL_CLASSES:
                c_data = best_record["val_per_class"].get(c_name, {})
                f.write(f"| **{c_name}** | {c_data.get('precision', 0):.2%} | {c_data.get('recall', 0):.2%} | {c_data.get('f1', 0):.4f} | {c_data.get('support', 0)} |\n")

            f.write("\n> [!NOTE]\n> Production readiness cannot be determined from training metrics alone. "
                    "Comprehensive out-of-sample evaluation on the official test split will be conducted in Phase 7.\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train NudgeWasteAI Four-Class Classifier")
    parser.add_argument("--epochs", type=int, default=default_training_config.epochs, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=default_training_config.batch_size, help="Batch size")
    parser.add_argument("--lr", type=float, default=default_training_config.learning_rate, help="Learning rate")
    parser.add_argument("--architecture", type=str, default=default_model_config.architecture, help="Model backbone")
    parser.add_argument("--max-samples", type=int, default=default_training_config.max_samples_per_class, help="Max samples per class")
    parser.add_argument("--seed", type=int, default=default_training_config.seed, help="Random seed")
    parser.add_argument("--no-pretrained", action="store_true", help="Disable ImageNet pretraining")
    args = parser.parse_args()

    data_cfg = DataConfig(batch_size=args.batch_size, seed=args.seed)
    model_cfg = ModelConfig(architecture=args.architecture, pretrained=not args.no_pretrained)
    train_cfg = TrainingConfig(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        max_samples_per_class=args.max_samples,
        seed=args.seed,
    )

    trainer = NudgeWasteTrainer(
        data_config=data_cfg,
        model_config=model_cfg,
        training_config=train_cfg,
    )
    results = trainer.train()
    print("\nTraining completed successfully! Best Model:", results["best_model_path"])


if __name__ == "__main__":
    main()
