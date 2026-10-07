"""
Unit Tests for NudgeWasteAI Model Architecture
==============================================

Tests:
1. Model creation and architecture initialization
2. Dummy input shape validation (B, 3, 224, 224)
3. Output tensor shape (B, 4)
4. Forward pass execution without training
5. Four-class prediction and probability outputs
6. Invalid input shape rejection
7. Backbone freezing and unfreezing
8. Model factory builder with ModelConfig
"""

import pytest

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from configs.config import (
    CANONICAL_CLASSES,
    NUM_CLASSES,
    ModelConfig,
    default_model_config,
)
from models.model import NudgeWasteClassifier, build_model


@pytest.mark.skipif(not HAS_TORCH, reason="PyTorch is required for model architecture tests")
class TestNudgeWasteModel:
    """Test suite for NudgeWasteClassifier."""

    def test_model_creation_default(self):
        """Verify default model creation (MobileNetV3-Small) with 4 output classes."""
        model = NudgeWasteClassifier(architecture="mobilenet_v3_small", num_classes=4, pretrained=False)
        assert isinstance(model, torch.nn.Module)
        assert model.num_classes == 4
        assert model.architecture == "mobilenet_v3_small"

        # Check parameter count: MobileNetV3-Small is lightweight (~1.5M params)
        params = model.count_parameters()
        assert params["total"] > 1_000_000
        assert params["total"] < 3_000_000
        assert params["trainable"] == params["total"]
        assert params["frozen"] == 0

    def test_model_creation_large_and_resnet(self):
        """Verify MobileNetV3-Large and ResNet-18 model instantiations."""
        # MobileNetV3-Large
        model_large = NudgeWasteClassifier(architecture="mobilenet_v3_large", num_classes=4, pretrained=False)
        assert model_large.num_classes == 4
        assert model_large.count_parameters()["total"] < 6_000_000

        # ResNet-18
        model_res = NudgeWasteClassifier(architecture="resnet18", num_classes=4, pretrained=False)
        assert model_res.num_classes == 4
        assert model_res.count_parameters()["total"] < 15_000_000

    def test_unsupported_architecture_raises(self):
        """Verify error is raised when an unknown architecture is requested."""
        with pytest.raises(ValueError, match="Unsupported architecture"):
            NudgeWasteClassifier(architecture="transformer_xyz_invalid", num_classes=4)

    def test_forward_pass_output_shape(self):
        """Verify forward pass on dummy inputs produces exact (B, 4) tensor."""
        model = NudgeWasteClassifier(architecture="mobilenet_v3_small", num_classes=4, pretrained=False)
        model.eval()

        batch_sizes = [1, 2, 4, 8]
        with torch.no_grad():
            for b in batch_sizes:
                dummy_input = torch.randn(b, 3, 224, 224, dtype=torch.float32)
                logits = model(dummy_input)

                # Output shape must be strictly (B, 4)
                assert isinstance(logits, torch.Tensor)
                assert logits.shape == (b, 4)
                assert logits.dtype == torch.float32

    def test_four_class_probabilities_and_predictions(self):
        """Verify predict_proba and predict return valid 4-class distributions and class names."""
        model = NudgeWasteClassifier(architecture="mobilenet_v3_small", num_classes=4, pretrained=False)
        model.eval()

        dummy_input = torch.randn(3, 3, 224, 224, dtype=torch.float32)

        # 1. Softmax probabilities
        with torch.no_grad():
            probs = model.predict_proba(dummy_input)
            assert probs.shape == (3, 4)
            # Each row must sum to 1.0 (within float tolerance)
            row_sums = torch.sum(probs, dim=-1)
            assert torch.allclose(row_sums, torch.ones(3), atol=1e-5)
            # All probabilities between 0 and 1
            assert (probs >= 0.0).all() and (probs <= 1.0).all()

        # 2. High-level predict() helper
        res = model.predict(dummy_input)
        assert "indices" in res
        assert "classes" in res
        assert "confidences" in res
        assert "probabilities" in res

        assert len(res["indices"]) == 3
        assert len(res["classes"]) == 3
        assert len(res["confidences"]) == 3

        for cls_name in res["classes"]:
            assert cls_name in CANONICAL_CLASSES

        for conf in res["confidences"]:
            assert 0.0 <= conf <= 1.0

    def test_invalid_input_shapes_rejection(self):
        """Verify invalid input dimensions or channel counts raise ValueError."""
        model = NudgeWasteClassifier(architecture="mobilenet_v3_small", num_classes=4, pretrained=False)

        # 3D input instead of 4D
        with pytest.raises(ValueError, match="Expected 4D input tensor"):
            model(torch.randn(3, 224, 224))

        # 1-channel grayscale instead of 3-channel RGB
        with pytest.raises(ValueError, match="Expected 3 color channels"):
            model(torch.randn(2, 1, 224, 224))

        # 4-channel RGBA instead of 3-channel RGB
        with pytest.raises(ValueError, match="Expected 3 color channels"):
            model(torch.randn(2, 4, 224, 224))

    def test_freeze_and_unfreeze_backbone(self):
        """Verify progressive transfer learning freeze/unfreeze functions."""
        model = NudgeWasteClassifier(architecture="mobilenet_v3_small", num_classes=4, pretrained=False)

        # Initially all parameters are trainable
        initial_params = model.count_parameters()
        assert initial_params["frozen"] == 0

        # 1. Freeze backbone with classifier head trainable
        model.freeze_backbone(only_last_layer=False)
        frozen_params = model.count_parameters()
        assert frozen_params["frozen"] > 0
        assert frozen_params["trainable"] < initial_params["total"]
        assert frozen_params["trainable"] == 594_948  # Classifier block parameters

        # 2. Freeze with only the final output layer trainable (1024 * 4 + 4 = 4100 parameters)
        model.freeze_backbone(only_last_layer=True)
        only_last_params = model.count_parameters()
        assert only_last_params["trainable"] == 4_100

        # 3. Unfreeze backbone completely
        model.unfreeze_backbone()
        unfrozen_params = model.count_parameters()
        assert unfrozen_params["frozen"] == 0
        assert unfrozen_params["trainable"] == initial_params["total"]

    def test_build_model_factory(self):
        """Verify factory function build_model with custom ModelConfig."""
        custom_cfg = ModelConfig(
            architecture="mobilenet_v3_small",
            num_classes=4,
            pretrained=False,
            dropout_rate=0.35,
        )
        model = build_model(config=custom_cfg)
        assert isinstance(model, NudgeWasteClassifier)
        assert model.num_classes == 4
        assert model.dropout_rate == 0.35

        # Override argument
        model_override = build_model(config=custom_cfg, architecture="mobilenet_v3_large")
        assert model_override.architecture == "mobilenet_v3_large"
