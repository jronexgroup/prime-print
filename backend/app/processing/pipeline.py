from pathlib import Path

from app.config import OUTPUT_DIR, PREVIEW_DIR
from app.processing.validator import validate_image
from app.processing.detector import detect_document, crop_to_document
from app.processing.perspective import correct_perspective
from app.processing.enhancer import enhance_for_print
from app.processing.classifier import classify_document
from app.processing.layout import get_profile, place_on_a4
from app.processing.pdf_gen import generate_pdf
from PIL import Image


def generate_preview(image: Image.Image, output_dir: str, document_id: str) -> str:
    preview_dir = Path(PREVIEW_DIR)
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview_path = preview_dir / f"{document_id}.jpg"

    thumb = image.copy()
    thumb.thumbnail((800, 800), Image.Resampling.LANCZOS)
    thumb.save(str(preview_path), "JPEG", quality=85)

    return str(preview_path)


def process_document(input_path: str) -> dict:
    document_id = Path(input_path).stem

    img = validate_image(input_path)

    points = detect_document(img)

    warped = correct_perspective(img, points)

    cropped = crop_to_document(warped, points)

    enhanced = enhance_for_print(cropped)

    doc_type, confidence = classify_document(enhanced)

    profile = get_profile(doc_type)

    a4_page = place_on_a4(enhanced, profile)

    pdf_path = generate_pdf(a4_page, str(OUTPUT_DIR), document_id)

    preview_path = generate_preview(a4_page, str(OUTPUT_DIR), document_id)

    return {
        "output_path": pdf_path,
        "preview_path": preview_path,
        "document_type": doc_type,
        "confidence": confidence,
    }
