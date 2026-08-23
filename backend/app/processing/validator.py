from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES


class ValidationError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def validate_image(file_path: str) -> Image.Image:
    path = Path(file_path)

    if not path.exists():
        raise ValidationError("FILE_NOT_FOUND", "File does not exist.")

    ext = path.suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            "INVALID_FILE_TYPE",
            f"File type '{ext}' is not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    size = path.stat().st_size
    if size > MAX_FILE_SIZE_BYTES:
        raise ValidationError(
            "FILE_TOO_LARGE",
            f"File size {size / (1024*1024):.1f}MB exceeds limit of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB.",
        )

    try:
        img = Image.open(path)
        img.verify()
        img = Image.open(path)
    except (UnidentifiedImageError, Exception):
        raise ValidationError("IMAGE_CORRUPTED", "File is not a valid image.")

    w, h = img.size
    if w < 600 or h < 800:
        raise ValidationError(
            "IMAGE_TOO_SMALL",
            f"Image resolution {w}x{h} is too small. Minimum is 600x800.",
        )

    exif = img.getexif()
    orientation_key = 0x0112
    if orientation_key in exif:
        orientation = exif[orientation_key]
        rotations = {3: 180, 6: 270, 8: 90}
        if orientation in rotations:
            img = img.rotate(rotations[orientation], expand=True)

    return img
