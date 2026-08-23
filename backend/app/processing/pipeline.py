from pathlib import Path

from app.config import OUTPUT_DIR, PREVIEW_DIR
from app.processing.validator import validate_image
from app.processing.detector import detect_document, crop_to_document
from app.processing.perspective import correct_perspective
from app.processing.enhancer import enhance_for_print
from app.processing.classifier import classify_document
from app.processing.layout import get_profile, place_on_a4
from app.processing.pdf_gen import generate_pdf
from app.processing.ai_analyzer import analyze_image
from PIL import Image
import cv2
import numpy as np


def generate_preview(image: Image.Image, output_dir: str, document_id: str) -> str:
    preview_dir = Path(PREVIEW_DIR)
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview_path = preview_dir / f"{document_id}.jpg"

    thumb = image.copy()
    thumb.thumbnail((800, 800), Image.Resampling.LANCZOS)
    thumb.save(str(preview_path), "JPEG", quality=85)

    return str(preview_path)


def _apply_rotation(image: Image.Image, degrees: float) -> Image.Image:
    if abs(degrees) < 0.5:
        return image
    return image.rotate(-degrees, expand=True, fillcolor=(255, 255, 255))


def _apply_crop(image: Image.Image, crop: dict) -> Image.Image:
    w, h = image.size
    x1 = int(crop["top_left_x"] * w)
    y1 = int(crop["top_left_y"] * h)
    x2 = int(crop["bottom_right_x"] * w)
    y2 = int(crop["bottom_right_y"] * h)

    x1 = max(0, min(x1, w - 1))
    y1 = max(0, min(y1, h - 1))
    x2 = max(x1 + 1, min(x2, w))
    y2 = max(y1 + 1, min(y2, h))

    return image.crop((x1, y1, x2, y2))


def _apply_brightness_contrast(image: Image.Image, brightness: int, contrast: int) -> Image.Image:
    arr = np.array(image, dtype=np.float32)

    # Brightness
    if brightness != 0:
        arr = arr + brightness

    # Contrast
    if contrast != 0:
        factor = 1.0 + (contrast / 100.0)
        mean = np.mean(arr)
        arr = (arr - mean) * factor + mean

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def process_document(input_path: str) -> dict:
    document_id = Path(input_path).stem

    img = validate_image(input_path)

    print(f"[PIPELINE] Analyzing image with AI...")
    ai_result = analyze_image(input_path)
    print(f"[PIPELINE] AI result: type={ai_result.get('document_type')}, visible={ai_result.get('is_document_visible')}, confidence={ai_result.get('confidence')}")

    # Apply AI instructions
    if ai_result.get("crop"):
        img = _apply_crop(img, ai_result["crop"])
        print(f"[PIPELINE] Cropped to {img.size}")

    if ai_result.get("rotation_degrees", 0) != 0:
        img = _apply_rotation(img, ai_result["rotation_degrees"])
        print(f"[PIPELINE] Rotated {ai_result['rotation_degrees']} degrees")

    brightness = ai_result.get("brightness_adjustment", 0)
    contrast = ai_result.get("contrast_adjustment", 0)
    if brightness != 0 or contrast != 0:
        img = _apply_brightness_contrast(img, brightness, contrast)
        print(f"[PIPELINE] Adjusted brightness={brightness}, contrast={contrast}")

    # Fallback: if AI didn't detect document well, try OpenCV detector
    if not ai_result.get("is_document_visible", True) and ai_result.get("confidence", 0) < 0.5:
        print(f"[PIPELINE] AI low confidence, trying OpenCV detector...")
        points = detect_document(img)
        if points is not None:
            img = crop_to_document(img, points)
            print(f"[PIPELINE] OpenCV cropped to {img.size}")

    # Enhance
    enhanced = enhance_for_print(img)

    # Classify
    doc_type = ai_result.get("document_type", "unknown")
    if doc_type == "unknown":
        ocr_type, confidence = classify_document(enhanced)
        if confidence > 0.3:
            doc_type = ocr_type

    # Load profile and place on A4
    profile = get_profile(doc_type)
    a4_page = place_on_a4(enhanced, profile)

    # Generate outputs
    pdf_path = generate_pdf(a4_page, str(OUTPUT_DIR), document_id)
    preview_path = generate_preview(a4_page, str(OUTPUT_DIR), document_id)

    return {
        "output_path": pdf_path,
        "preview_path": preview_path,
        "document_type": doc_type,
        "confidence": ai_result.get("confidence", 0.0),
    }
