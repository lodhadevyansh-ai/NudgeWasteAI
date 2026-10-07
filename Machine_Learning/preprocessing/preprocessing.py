"""
Unified Image Preprocessing Module for NudgeWasteAI
===================================================

This module provides deterministic image validation, format normalization,
resizing (with optional aspect-ratio preserving letterboxing), and standardization
(ImageNet mean & std) for the NudgeWasteAI 4-class classifier.

Features:
---------
- Robust image validation (corrupt, truncated, empty, or unreadable files).
- Multi-mode format conversion (RGBA, CMYK, Palette, Grayscale -> 3-channel RGB).
- Alpha channel compositing (composites transparent images onto a neutral background).
- Configurable resizing with letterboxing to prevent aspect ratio distortion.
- ImageNet normalization: mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225].
- Dual-mode output: returns torch.Tensor (when PyTorch is available) or NumPy ndarray.
- Safe execution: graceful error capture without pipeline disruption.
"""

import os
from pathlib import Path
from typing import Optional, Tuple, Union
import numpy as np
from PIL import Image, ImageOps, ImageFile

# Allow PIL to handle slightly truncated images without throwing silent exceptions
setattr(ImageFile, "LOAD_TRUNCATED_IMAGES", True)

# Optional PyTorch support
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


# Default ImageNet normalization constants (standard for PyTorch/Torchvision backbones)
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

DEFAULT_IMAGE_SIZE = (224, 224)


def validate_image(image_input: Union[str, Path, bytes, Image.Image]) -> Tuple[bool, Optional[str]]:
    """
    Validate that an image input exists, is non-empty, and can be read and decoded.

    Args:
        image_input: File path (str/Path), raw bytes, or PIL Image object.

    Returns:
        Tuple of (is_valid: bool, error_reason: Optional[str]).
    """
    if image_input is None:
        return False, "Image input is None."

    if isinstance(image_input, Image.Image):
        try:
            w, h = image_input.size
            if w <= 0 or h <= 0:
                return False, f"Invalid image dimensions: {w}x{h}."
            return True, None
        except Exception as e:
            return False, f"Failed to inspect PIL image: {str(e)}"

    if isinstance(image_input, (str, Path)):
        p = Path(image_input)
        if not p.exists():
            return False, f"File does not exist: {p}"
        if not p.is_file():
            return False, f"Path is not a regular file: {p}"
        try:
            size_bytes = p.stat().st_size
            if size_bytes == 0:
                return False, f"File is empty (0 bytes): {p}"
        except Exception as e:
            return False, f"Failed to check file size: {str(e)}"

        try:
            with Image.open(p) as img:
                img.verify()
            # After verify(), image must be re-opened for reading data
            with Image.open(p) as img:
                img.load()
                w, h = img.size
                if w <= 0 or h <= 0:
                    return False, f"Invalid dimensions: {w}x{h}."
            return True, None
        except Exception as e:
            return False, f"Corrupted or unreadable image file: {str(e)}"

    if isinstance(image_input, bytes):
        if len(image_input) == 0:
            return False, "Byte buffer is empty (0 bytes)."
        try:
            import io
            with Image.open(io.BytesIO(image_input)) as img:
                img.verify()
            with Image.open(io.BytesIO(image_input)) as img:
                img.load()
                w, h = img.size
                if w <= 0 or h <= 0:
                    return False, f"Invalid dimensions: {w}x{h}."
            return True, None
        except Exception as e:
            return False, f"Corrupted byte stream: {str(e)}"

    return False, f"Unsupported image input type: {type(image_input)}"


def handle_image_format(img: Image.Image, background_color: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    """
    Convert any PIL Image format/mode into standard 3-channel RGB.

    Properly composites alpha channels (RGBA, LA) onto background_color to prevent
    black borders or transparency artifacts.

    Args:
        img: Input PIL Image.
        background_color: RGB tuple for alpha compositing (default: white).

    Returns:
        Standardized 3-channel RGB PIL Image.
    """
    if img.mode == "RGB":
        return img

    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        background = Image.new("RGBA", rgba.size, background_color + (255,))
        composited = Image.alpha_composite(background, rgba)
        return composited.convert("RGB")

    return img.convert("RGB")


def resize_image(
    img: Image.Image,
    target_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE,
    keep_aspect_ratio: bool = True,
    pad_color: Tuple[int, int, int] = (0, 0, 0),
) -> Image.Image:
    """
    Resize a PIL Image to target_size.

    Args:
        img: Input RGB PIL Image.
        target_size: Desired (width, height) tuple (default: 224, 224).
        keep_aspect_ratio: If True, scales proportionally and pads to target_size (letterboxing).
                           If False, resizes directly (may stretch/squash).
        pad_color: RGB color for padding borders when keep_aspect_ratio is True.

    Returns:
        Resized PIL Image of exact dimensions target_size.
    """
    target_w, target_h = target_size

    if not keep_aspect_ratio:
        return img.resize((target_w, target_h), Image.Resampling.BICUBIC)

    orig_w, orig_h = img.size
    if orig_w == target_w and orig_h == target_h:
        return img

    # Compute scale to fit within target bounding box
    scale = min(target_w / orig_w, target_h / orig_h)
    new_w = max(1, round(orig_w * scale))
    new_h = max(1, round(orig_h * scale))

    resized = img.resize((new_w, new_h), Image.Resampling.BICUBIC)

    # Letterbox onto target canvas
    canvas = Image.new("RGB", (target_w, target_h), pad_color)
    paste_x = (target_w - new_w) // 2
    paste_y = (target_h - new_h) // 2
    canvas.paste(resized, (paste_x, paste_y))
    return canvas


def normalize_image(
    img: Image.Image,
    mean: np.ndarray = IMAGENET_MEAN,
    std: np.ndarray = IMAGENET_STD,
    return_tensor: bool = True,
) -> Union["torch.Tensor", np.ndarray]:
    """
    Convert a PIL Image to float32, scale to [0, 1], and apply channel normalization:
        normalized = (image / 255.0 - mean) / std

    Args:
        img: Input RGB PIL Image.
        mean: Channel means (length 3).
        std: Channel standard deviations (length 3).
        return_tensor: If True and PyTorch is available, returns torch.Tensor of shape (3, H, W).
                       Otherwise returns NumPy ndarray of shape (3, H, W).

    Returns:
        Normalized array or tensor with shape (3, H, W), float32.
    """
    arr = np.array(img, dtype=np.float32) / 255.0  # shape: (H, W, 3), range [0, 1]

    # Normalize: (arr - mean) / std across channels
    arr = (arr - mean) / std

    # Transpose from (H, W, C) to (C, H, W)
    arr = np.transpose(arr, (2, 0, 1)).astype(np.float32)

    if return_tensor and HAS_TORCH:
        return torch.from_numpy(arr)

    return arr


def denormalize_image(
    tensor_or_np: Union["torch.Tensor", np.ndarray],
    mean: np.ndarray = IMAGENET_MEAN,
    std: np.ndarray = IMAGENET_STD,
) -> Image.Image:
    """
    Invert normalization and convert a (3, H, W) tensor/array back to a viewable PIL Image.
    Useful for visualization, debugging, and testing.
    """
    if HAS_TORCH and isinstance(tensor_or_np, torch.Tensor):
        arr = tensor_or_np.detach().cpu().numpy()
    else:
        arr = np.array(tensor_or_np)

    # Transpose from (C, H, W) back to (H, W, C)
    if arr.ndim == 3 and arr.shape[0] == 3:
        arr = np.transpose(arr, (1, 2, 0))

    # Invert: arr * std + mean
    arr = arr * std + mean
    arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, mode="RGB")


class ImagePreprocessor:
    """
    Unified, deterministic preprocessor for NudgeWasteAI classification.

    Applies:
        1. Validation
        2. Format standardization (RGB)
        3. Optional bounding box crop (for datasets like TACO)
        4. Resizing with aspect-ratio preservation
        5. Scaling and ImageNet normalization
    """

    def __init__(
        self,
        target_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE,
        keep_aspect_ratio: bool = True,
        mean: np.ndarray = IMAGENET_MEAN,
        std: np.ndarray = IMAGENET_STD,
        return_tensor: bool = True,
    ):
        self.target_size = target_size
        self.keep_aspect_ratio = keep_aspect_ratio
        self.mean = np.array(mean, dtype=np.float32)
        self.std = np.array(std, dtype=np.float32)
        self.return_tensor = return_tensor

    def preprocess(
        self,
        image_input: Union[str, Path, bytes, Image.Image],
        bbox: Optional[Tuple[float, float, float, float]] = None,
    ) -> Union["torch.Tensor", np.ndarray]:
        """
        Preprocess an image or raise an informative ValueError.

        Args:
            image_input: Path, bytes, or PIL Image.
            bbox: Optional bounding box [x, y, width, height] in original pixel coordinates.

        Returns:
            Normalized tensor/array with shape (3, target_h, target_w).
        """
        is_valid, error = validate_image(image_input)
        if not is_valid:
            raise ValueError(f"Image validation failed: {error}")

        if isinstance(image_input, (str, Path)):
            img = Image.open(image_input)
        elif isinstance(image_input, bytes):
            import io
            img = Image.open(io.BytesIO(image_input))
        else:
            img = image_input

        # Crop bounding box if provided (e.g. for TACO objects)
        if bbox is not None:
            x, y, w, h = bbox
            img_w, img_h = img.size
            x1 = max(0, round(x))
            y1 = max(0, round(y))
            x2 = min(img_w, round(x + w))
            y2 = min(img_h, round(y + h))
            if x2 > x1 and y2 > y1:
                img = img.crop((x1, y1, x2, y2))

        # Format handling: Convert to 3-channel RGB
        img_rgb = handle_image_format(img)

        # Resize with optional letterboxing
        resized = resize_image(
            img_rgb,
            target_size=self.target_size,
            keep_aspect_ratio=self.keep_aspect_ratio,
        )

        # Normalize and convert to float32 (3, H, W)
        return normalize_image(
            resized,
            mean=self.mean,
            std=self.std,
            return_tensor=self.return_tensor,
        )

    def preprocess_safe(
        self,
        image_input: Union[str, Path, bytes, Image.Image],
        bbox: Optional[Tuple[float, float, float, float]] = None,
    ) -> Tuple[Optional[Union["torch.Tensor", np.ndarray]], Optional[str]]:
        """
        Safe version of preprocess: returns (result, None) on success or (None, error_str) on failure.
        Ensures pipelines do not terminate abruptly due to corrupt inputs.
        """
        try:
            result = self.preprocess(image_input, bbox=bbox)
            return result, None
        except Exception as e:
            return None, str(e)


# Default module-level preprocessor instance for convenience
default_preprocessor = ImagePreprocessor()
