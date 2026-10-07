import base64
import io
import sys
from pathlib import Path
from PIL import Image, ImageDraw

# Add Machine_Learning and backend to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "Machine_Learning"))
sys.path.insert(0, str(project_root / "backend"))

from inference.bin_verifier import bin_verifier, _rgb_to_hsv, _generate_synthetic_bin_image

def create_real_green_bin_photo(shade="outdoor_leaf_green"):
    """Creates synthetic realistic images representing various real green dustbins."""
    img = Image.new("RGB", (600, 600), color=(220, 220, 215)) # Grey outdoor background
    draw = ImageDraw.Draw(img)
    
    if shade == "dark_forest_green":
        # Municipal dark green bin: RGB ~ (25, 100, 35) -> HSV ~ (128, 0.75, 0.39)
        color = (25, 100, 35)
        rim_color = (15, 75, 25)
    elif shade == "bright_green":
        # Bright lime/green bin: RGB ~ (40, 180, 50) -> HSV ~ (124, 0.77, 0.70)
        color = (40, 180, 50)
        rim_color = (30, 140, 40)
    elif shade == "yellow_green":
        # Yellowish green bin: RGB ~ (120, 170, 40) -> HSV ~ (83, 0.76, 0.66)
        color = (120, 170, 40)
        rim_color = (90, 130, 30)
    elif shade == "olive_green":
        # Olive green bin under shadow: RGB ~ (70, 90, 40) -> HSV ~ (84, 0.55, 0.35)
        color = (70, 90, 40)
        rim_color = (50, 65, 30)
    else: # standard leaf green
        color = (35, 155, 55)
        rim_color = (25, 115, 40)
        
    # Draw dustbin geometry (lid + body)
    draw.polygon([(150, 180), (450, 180), (410, 520), (190, 520)], fill=color, outline=(40, 40, 40))
    draw.rectangle([130, 140, 470, 180], fill=rim_color, outline=(30, 30, 30))
    # Add recycle bin symbol / detail lines
    draw.line([(250, 250), (350, 250)], fill=(255, 255, 255), width=5)
    draw.line([(300, 250), (300, 400)], fill=(255, 255, 255), width=5)
    
    return img

def image_to_base64(img: Image.Image, format="JPEG") -> str:
    buf = io.BytesIO()
    img.save(buf, format=format)
    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/{format.lower()};base64,{b64}"

def run_diagnostics():
    print("--- DIAGNOSTIC TEST RUN ---")
    shades = ["dark_forest_green", "bright_green", "yellow_green", "olive_green", "standard_leaf_green"]
    
    for shade in shades:
        img = create_real_green_bin_photo(shade)
        b64_str = image_to_base64(img)
        
        # Verify directly with bin_verifier
        res = bin_verifier.verify(b64_str, expected_category="Wet")
        
        print(f"\nShade: {shade}")
        print(f"Verified: {res.get('verified')}")
        print(f"Status: {res.get('verification', {}).get('status')}")
        print(f"Detected Bin: {res.get('verification', {}).get('detected_bin')}")
        print(f"Detected Color: {res.get('detected_bin_color')}")
        print(f"Confidence: {res.get('confidence')}")
        print(f"Message: {res.get('message')}")

if __name__ == "__main__":
    run_diagnostics()
