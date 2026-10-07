"""
Model Export & Optimization Tool for NudgeWasteAI
=================================================

Converts trained PyTorch model checkpoints (.pt) into optimized TorchScript (.torchscript.pt)
and optional ONNX (.onnx) formats suitable for edge, mobile, and lightweight production deployment.

Key Features:
-------------
- TorchScript Tracing: Compiles model computational graph for C++/Mobile/Edge runtime without Python dependency.
- Deterministic Output Verification: Ensures exported graph outputs match PyTorch predictions within tight tolerance.
- Non-Destructive: Original PyTorch state dict checkpoint is strictly preserved.
"""

import argparse
import json
import logging
from pathlib import Path
import sys
from typing import Dict, Tuple, cast

# Ensure Machine_Learning root is on sys.path
_ml_root = str(Path(__file__).resolve().parent.parent)
if _ml_root not in sys.path:
    sys.path.insert(0, _ml_root)

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from configs.config import NUM_CLASSES, TRAINED_MODELS_DIR
from models.model import build_model
from preprocessing.preprocessing import DEFAULT_IMAGE_SIZE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def export_torchscript(
    checkpoint_path: Path,
    output_path: Path,
    input_shape: Tuple[int, int, int, int] = (1, 3, DEFAULT_IMAGE_SIZE[0], DEFAULT_IMAGE_SIZE[1]),
) -> Path:
    """
    Exports PyTorch model checkpoint to TorchScript via tracing.
    """
    logger.info(f"Loading PyTorch checkpoint from: {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    architecture = checkpoint.get("architecture", "mobilenet_v3_small")
    num_classes = checkpoint.get("num_classes", NUM_CLASSES)

    model = build_model(architecture=architecture, num_classes=num_classes, pretrained=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    dummy_input = torch.randn(*input_shape)

    # Perform PyTorch inference for reference
    with torch.no_grad():
        original_output = model(dummy_input)

    logger.info(f"Tracing model computational graph with input shape {input_shape}...")
    traced_model = cast(torch.jit.ScriptModule, torch.jit.trace(model, dummy_input))
    traced_model.eval()

    # Verify traced output matches original
    with torch.no_grad():
        traced_output = traced_model(dummy_input)

    diff = torch.max(torch.abs(original_output - traced_output)).item()
    if diff > 1e-4:
        raise ValueError(f"TorchScript verification failed! Max output difference: {diff:.6f}")
    logger.info(f"TorchScript export verified successfully! Max difference vs PyTorch: {diff:.8f}")

    # Save traced model
    output_path.parent.mkdir(parents=True, exist_ok=True)
    traced_model.save(str(output_path))

    orig_size_mb = checkpoint_path.stat().st_size / (1024 * 1024)
    ts_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"Saved TorchScript model to: {output_path}")
    logger.info(f"Model size: Full Checkpoint={orig_size_mb:.2f} MB -> TorchScript={ts_size_mb:.2f} MB")

    return output_path


def export_onnx_optional(
    checkpoint_path: Path,
    output_path: Path,
    input_shape: Tuple[int, int, int, int] = (1, 3, DEFAULT_IMAGE_SIZE[0], DEFAULT_IMAGE_SIZE[1]),
) -> bool:
    """
    Attempts optional ONNX export if onnx module is available.
    """
    try:
        import onnx  # type: ignore # pyrefly: ignore [missing-import]
    except ImportError:
        logger.info("ONNX package not installed. Skipping optional ONNX export.")
        return False

    try:
        logger.info(f"Exporting ONNX model to: {output_path}")
        checkpoint = torch.load(checkpoint_path, map_location="cpu")
        model = build_model(
            architecture=checkpoint.get("architecture", "mobilenet_v3_small"),
            num_classes=checkpoint.get("num_classes", NUM_CLASSES),
            pretrained=False,
        )
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()

        dummy_input = torch.randn(*input_shape)
        torch.onnx.export(
            model,
            (dummy_input,),
            str(output_path),
            export_params=True,
            opset_version=14,
            do_constant_folding=True,
            input_names=["input"],
            output_names=["logits"],
            dynamic_axes={"input": {0: "batch_size"}, "logits": {0: "batch_size"}},
        )

        onnx_model = onnx.load(str(output_path))
        onnx.checker.check_model(onnx_model)
        logger.info(f"ONNX export succeeded and validated at: {output_path}")
        return True
    except Exception as e:
        logger.warning(f"ONNX export failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Export NudgeWasteAI trained model to deployment formats.")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=str(TRAINED_MODELS_DIR / "nudgewaste_mobilenetv3_small_best.pt"),
        help="Path to trained PyTorch checkpoint",
    )
    args = parser.parse_args()

    ckpt_path = Path(args.checkpoint).resolve()
    if not ckpt_path.exists():
        logger.error(f"Checkpoint not found at: {ckpt_path}")
        sys.exit(1)

    ts_output_path = TRAINED_MODELS_DIR / "nudgewaste_mobilenetv3_small.torchscript.pt"
    onnx_output_path = TRAINED_MODELS_DIR / "nudgewaste_mobilenetv3_small.onnx"

    logger.info("==================================================")
    logger.info("STARTING NUDGEWASTEAI MODEL EXPORT & OPTIMIZATION")
    logger.info("==================================================")

    export_torchscript(ckpt_path, ts_output_path)
    export_onnx_optional(ckpt_path, onnx_output_path)

    logger.info("==================================================")
    logger.info("MODEL EXPORT & OPTIMIZATION COMPLETED SUCCESSFULLY")
    logger.info("==================================================")


if __name__ == "__main__":
    main()
