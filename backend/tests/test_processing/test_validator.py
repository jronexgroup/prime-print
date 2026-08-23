import io
import pytest
from PIL import Image

from app.processing.validator import validate_image, ValidationError


def create_test_image(tmp_path, size=(1024, 1024), format="PNG"):
    img = Image.new("RGB", size, color=(128, 128, 128))
    path = tmp_path / "test_image.png"
    img.save(str(path), format)
    return str(path)


def test_validate_valid_image(tmp_path):
    path = create_test_image(tmp_path)
    result = validate_image(path)
    assert result.size == (1024, 1024)


def test_validate_too_small(tmp_path):
    img = Image.new("RGB", (100, 100), color=(128, 128, 128))
    path = tmp_path / "small.png"
    img.save(str(path))

    with pytest.raises(ValidationError) as exc_info:
        validate_image(str(path))
    assert exc_info.value.code == "IMAGE_TOO_SMALL"


def test_validate_nonexistent_file():
    with pytest.raises(ValidationError) as exc_info:
        validate_image("/nonexistent/file.png")
    assert exc_info.value.code == "FILE_NOT_FOUND"
