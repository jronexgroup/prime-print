"""Quick test: validate + detect a document from an image."""
import sys
sys.path.insert(0, "/root/projects/prime-print/backend")

from PIL import Image, ImageDraw
import numpy as np

# Create a fake document image (white rectangle on dark background)
def create_test_doc():
    img = Image.new("RGB", (1200, 1600), (50, 50, 50))  # dark bg
    draw = ImageDraw.Draw(img)
    # white document in center
    draw.rectangle([200, 300, 1000, 1300], fill=(240, 240, 240), outline=(0, 0, 0), width=3)
    # some text-like lines
    for y in range(400, 1200, 80):
        draw.rectangle([250, y, 950, y + 10], fill=(80, 80, 80))
    path = "/tmp/test_document.png"
    img.save(path)
    return path

# Step 1: Validate
from app.processing.validator import validate_image

img_path = create_test_doc()
print(f"=== VALIDATOR ===")
print(f"Input: {img_path}")
img = validate_image(img_path)
print(f"Result: OK — size {img.size}, mode {img.mode}")

# Step 2: Detect boundary
from app.processing.detector import detect_document, crop_to_document

print(f"\n=== DETECTOR ===")
points = detect_document(img)
if points is not None:
    print(f"Detected 4 corner points:")
    for i, p in enumerate(points):
        labels = ["top-left", "top-right", "bottom-right", "bottom-left"]
        print(f"  {labels[i]}: ({p[0]:.0f}, {p[1]:.0f})")
    cropped = crop_to_document(img, points)
    print(f"Cropped size: {cropped.size}")
    cropped.save("/tmp/test_cropped.png")
    print(f"Saved: /tmp/test_cropped.png")
else:
    print("No document boundary detected (fallback to full image)")

# Step 3: Enhance
from app.processing.enhancer import enhance_for_print

print(f"\n=== ENHANCER ===")
enhanced = enhance_for_print(img)
print(f"Enhanced size: {enhanced.size}, mode {enhanced.mode}")
enhanced.save("/tmp/test_enhanced.png")
print(f"Saved: /tmp/test_enhanced.png")

# Step 4: Full pipeline
from app.processing.pipeline import process_document

print(f"\n=== FULL PIPELINE ===")
result = process_document(img_path)
print(f"Document type: {result['document_type']}")
print(f"Confidence: {result['confidence']}")
print(f"PDF: {result['output_path']}")
print(f"Preview: {result['preview_path']}")

print(f"\n✅ All steps passed!")
