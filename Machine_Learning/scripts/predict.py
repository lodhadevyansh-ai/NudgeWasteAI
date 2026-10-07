"""
CLI Script Entry Point for NudgeWasteAI Inference
=================================================
Convenient command-line script to run predictions on single waste images.
"""

# pyrefly: ignore [missing-import]

import argparse
import json
from pathlib import Path
import sys

# Ensure Machine_Learning root is on sys.path
_ml_root = str(Path(__file__).resolve().parent.parent)
if _ml_root not in sys.path:
    sys.path.insert(0, _ml_root)

from inference.predictor import NudgeWastePredictor, predict_image


def main():
    parser = argparse.ArgumentParser(description="Run NudgeWasteAI classification on an image.")
    parser.add_argument("--image", type=str, required=True, help="Path to input waste image")
    parser.add_argument("--checkpoint", type=str, default=None, help="Optional custom checkpoint path")
    args = parser.parse_args()

    if args.checkpoint:
        predictor = NudgeWastePredictor(checkpoint_path=args.checkpoint)
        res = predictor.predict(args.image)
    else:
        res = predict_image(args.image)

    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
