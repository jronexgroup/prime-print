from pathlib import Path

import img2pdf
from PIL import Image


def generate_pdf(image: Image.Image, output_dir: str, document_id: str) -> str:
    output_path = Path(output_dir) / f"{document_id}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = Path(output_dir) / f"{document_id}_temp.png"
    image.save(str(temp_path), "PNG", dpi=(300, 300))

    with open(temp_path, "rb") as f:
        pdf_bytes = img2pdf.convert(f.read())

    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    temp_path.unlink(missing_ok=True)

    return str(output_path)
