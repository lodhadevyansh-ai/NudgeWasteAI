"""
NudgeWasteAI Model Architecture
===============================

Implements the lightweight image classification architecture for the NudgeWasteAI
four-class waste classification problem:
    1. Wet
    2. Dry
    3. Sanitary
    4. Special Care

Architecture Choice: MobileNetV3-Small (default) & MobileNetV3-Large
-------------------------------------------------------------------
- MobileNetV3-Small is chosen as the primary architecture because it is specifically
  designed for edge and mobile on-device deployment (smart bins, mobile phones, IoT).
- Lightweight footprint: ~1.52 million parameters (Small) / ~4.21 million (Large).
- Extremely low latency (<10 ms on standard mobile/edge CPU).
- Utilizes inverted residual blocks, depthwise separable convolutions, hard-swish,
  and Squeeze-and-Excitation (SE) attention mechanisms for high visual expressiveness.
- Supports progressive transfer learning via freeze_backbone() and unfreeze_backbone().
- The final classification head produces strictly four output logits corresponding
  to the canonical waste streams.
"""

from typing import Any, Dict, List, Optional, Tuple, Union, TYPE_CHECKING
import logging

from configs.config import (
    CANONICAL_CLASSES,
    IDX_TO_CLASS,
    NUM_CLASSES,
    ModelConfig,
    default_model_config,
)

logger = logging.getLogger(__name__)

# Optional PyTorch support
if TYPE_CHECKING:
    import torch
    import torch.nn as nn
    import torchvision.models as tv_models
    from torchvision.models import (
        MobileNet_V3_Small_Weights,
        MobileNet_V3_Large_Weights,
        ResNet18_Weights,
    )
    HAS_TORCH = True
    BaseModel = nn.Module
else:
    try:
        import torch
        import torch.nn as nn
        import torchvision.models as tv_models
        from torchvision.models import (
            MobileNet_V3_Small_Weights,
            MobileNet_V3_Large_Weights,
            ResNet18_Weights,
        )
        HAS_TORCH = True
        BaseModel = nn.Module
    except ImportError:
        HAS_TORCH = False
        BaseModel = object


class NudgeWasteClassifier(BaseModel):
    """
    Lightweight 4-class classifier for NudgeWasteAI.
    """

    SUPPORTED_ARCHITECTURES = ("mobilenet_v3_small", "mobilenet_v3_large", "resnet18")

    def __init__(
        self,
        architecture: str = "mobilenet_v3_small",
        num_classes: int = NUM_CLASSES,
        pretrained: bool = False,
        dropout_rate: float = 0.20,
    ):
        if not HAS_TORCH:
            raise ImportError(
                "PyTorch and TorchVision are required to instantiate NudgeWasteClassifier. "
                "Please run with the project virtual environment (e.g. .venv)."
            )

        super().__init__()
        self.architecture = architecture.lower()
        self.num_classes = num_classes
        self.pretrained = pretrained
        self.dropout_rate = dropout_rate

        if self.architecture not in self.SUPPORTED_ARCHITECTURES:
            raise ValueError(
                f"Unsupported architecture: '{architecture}'. "
                f"Supported architectures are: {self.SUPPORTED_ARCHITECTURES}"
            )

        self._build_backbone()

    def _build_backbone(self) -> None:
        """
        Instantiate the backbone network and replace the final classification head
        to produce strictly self.num_classes output logits.
        """
        if self.architecture == "mobilenet_v3_small":
            weights = None
            if self.pretrained:
                try:
                    weights = MobileNet_V3_Small_Weights.DEFAULT
                except Exception as e:
                    logger.warning(f"Could not load pretrained weights for MobileNetV3-Small: {e}. Initializing randomly.")

            self.backbone = tv_models.mobilenet_v3_small(weights=weights)

            # MobileNetV3-Small classifier has 4 layers:
            # Linear(576, 1024) -> Hardswish -> Dropout(0.2) -> Linear(1024, 1000)
            in_features = int(getattr(self.backbone.classifier[-1], "in_features"))
            self.backbone.classifier[-1] = nn.Linear(in_features, self.num_classes)

        elif self.architecture == "mobilenet_v3_large":
            weights = None
            if self.pretrained:
                try:
                    weights = MobileNet_V3_Large_Weights.DEFAULT
                except Exception as e:
                    logger.warning(f"Could not load pretrained weights for MobileNetV3-Large: {e}. Initializing randomly.")

            self.backbone = tv_models.mobilenet_v3_large(weights=weights)

            in_features = int(getattr(self.backbone.classifier[-1], "in_features"))
            self.backbone.classifier[-1] = nn.Linear(in_features, self.num_classes)

        elif self.architecture == "resnet18":
            weights = None
            if self.pretrained:
                try:
                    weights = ResNet18_Weights.DEFAULT
                except Exception as e:
                    logger.warning(f"Could not load pretrained weights for ResNet-18: {e}. Initializing randomly.")

            self.backbone = tv_models.resnet18(weights=weights)
            in_features = self.backbone.fc.in_features
            setattr(
                self.backbone,
                "fc",
                nn.Sequential(
                    nn.Dropout(p=self.dropout_rate),
                    nn.Linear(in_features, self.num_classes),
                ),
            )

    def forward(self, x: "torch.Tensor") -> "torch.Tensor":
        """
        Forward pass.

        Args:
            x: Input tensor of shape (B, 3, H, W).

        Returns:
            Logits tensor of shape (B, 4).
        """
        if x.dim() != 4:
            raise ValueError(f"Expected 4D input tensor (B, C, H, W), got {x.dim()}D tensor.")
        if x.shape[1] != 3:
            raise ValueError(f"Expected 3 color channels (C=3), got {x.shape[1]} channels.")

        return self.backbone(x)

    def predict_proba(self, x: "torch.Tensor") -> "torch.Tensor":
        """
        Compute softmax probabilities for input tensor.

        Returns:
            Probability tensor of shape (B, 4).
        """
        logits = self.forward(x)
        return torch.softmax(logits, dim=-1)

    def predict(self, x: "torch.Tensor") -> Dict[str, Any]:
        """
        High-level inference helper returning class predictions, confidence scores,
        and canonical class names.
        """
        self.eval()
        with torch.no_grad():
            probs = self.predict_proba(x)
            confidences, pred_indices = torch.max(probs, dim=-1)

        pred_idx_list = pred_indices.cpu().tolist()
        conf_list = confidences.cpu().tolist()
        class_names = [IDX_TO_CLASS[idx] for idx in pred_idx_list]

        return {
            "indices": pred_idx_list,
            "classes": class_names,
            "confidences": conf_list,
            "probabilities": probs.cpu().tolist(),
        }

    def freeze_backbone(self, only_last_layer: bool = False) -> None:
        """
        Freeze backbone feature extractor parameters.

        Args:
            only_last_layer: If True, only the final Linear layer remains trainable.
                             If False, the entire classification head is trainable.
        """
        for param in self.backbone.parameters():
            param.requires_grad = False

        classifier = getattr(self.backbone, "classifier", None)
        fc = getattr(self.backbone, "fc", None)

        if isinstance(classifier, nn.Module):
            if only_last_layer:
                children = list(classifier.children())
                if children:
                    for param in children[-1].parameters():
                        param.requires_grad = True
            else:
                for param in classifier.parameters():
                    param.requires_grad = True
        elif isinstance(fc, nn.Module):
            for param in fc.parameters():
                param.requires_grad = True

        logger.info(f"Backbone frozen. Trainable parameters: {self.count_parameters()['trainable']:,}")

    def unfreeze_backbone(self) -> None:
        """
        Unfreeze all parameters across the entire network for full fine-tuning.
        """
        for param in self.backbone.parameters():
            param.requires_grad = True
        logger.info(f"Backbone unfrozen. Trainable parameters: {self.count_parameters()['trainable']:,}")

    def count_parameters(self) -> Dict[str, int]:
        """
        Count total, trainable, and frozen parameters.
        """
        total = sum(p.numel() for p in self.parameters())
        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        frozen = total - trainable
        return {
            "total": total,
            "trainable": trainable,
            "frozen": frozen,
        }


def build_model(
    config: Optional[ModelConfig] = None,
    architecture: Optional[str] = None,
    num_classes: Optional[int] = None,
    pretrained: Optional[bool] = None,
    dropout_rate: Optional[float] = None,
) -> NudgeWasteClassifier:
    """
    Factory function to construct a NudgeWasteClassifier.

    Args:
        config: ModelConfig instance (default: default_model_config).
        architecture: Optional override for backbone name.
        num_classes: Optional override for output count (default: 4).
        pretrained: Optional override for pretrained weights.
        dropout_rate: Optional override for dropout rate.

    Returns:
        Configured NudgeWasteClassifier instance.
    """
    cfg = config or default_model_config

    eff_arch = architecture if architecture is not None else cfg.architecture
    eff_classes = num_classes if num_classes is not None else cfg.num_classes
    eff_pretrained = pretrained if pretrained is not None else cfg.pretrained
    eff_dropout = dropout_rate if dropout_rate is not None else cfg.dropout_rate

    return NudgeWasteClassifier(
        architecture=eff_arch,
        num_classes=eff_classes,
        pretrained=eff_pretrained,
        dropout_rate=eff_dropout,
    )
