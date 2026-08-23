import json
from pathlib import Path
from typing import Dict

from app.config import A4_HEIGHT_PX, A4_WIDTH_PX, DPI
from PIL import Image

PROFILES_DIR = Path(__file__).parent.parent / "profiles"


def load_profiles() -> Dict[str, dict]:
    profiles = {}
    if not PROFILES_DIR.exists():
        return profiles
    for f in PROFILES_DIR.glob("*.json"):
        with open(f) as fh:
            data = json.load(fh)
            doc_id = data.get("document_id", f.stem)
            profiles[doc_id] = data
    return profiles


def get_profile(document_type: str) -> dict:
    profiles = load_profiles()
    return profiles.get(document_type, _default_profile())


def _default_profile() -> dict:
    return {
        "document_name": "Unknown Document",
        "document_id": "unknown",
        "target_width_px": 1063,
        "target_height_px": 674,
        "margin_px": 37,
        "color_mode": "grayscale",
    }


def place_on_a4(image: Image.Image, profile: dict) -> Image.Image:
    if image.mode == "L":
        canvas = Image.new("L", (A4_WIDTH_PX, A4_HEIGHT_PX), 255)
    else:
        canvas = Image.new("RGB", (A4_WIDTH_PX, A4_HEIGHT_PX), (255, 255, 255))

    target_w = profile.get("target_width_px", 1063)
    target_h = profile.get("target_height_px", 674)
    margin = profile.get("margin_px", 37)

    available_w = A4_WIDTH_PX - (2 * margin)
    available_h = A4_HEIGHT_PX - (2 * margin)

    img_w, img_h = image.size
    scale_w = available_w / img_w
    scale_h = available_h / img_h
    scale = min(scale_w, scale_h, 1.0)

    new_w = int(img_w * scale)
    new_h = int(img_h * scale)

    resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    x = (A4_WIDTH_PX - new_w) // 2
    y = (A4_HEIGHT_PX - new_h) // 2

    if resized.mode != canvas.mode:
        if canvas.mode == "L" and resized.mode == "RGB":
            resized = resized.convert("L")
        elif canvas.mode == "RGB" and resized.mode == "L":
            resized = resized.convert("RGB")

    canvas.paste(resized, (x, y))

    return canvas
