import pytest
from PIL import Image

from app.processing.layout import get_profile, place_on_a4


def test_get_profile_aadhaar():
    profile = get_profile("aadhaar")
    assert profile["document_id"] == "aadhaar"
    assert profile["target_width_px"] == 1063
    assert profile["target_height_px"] == 674


def test_get_profile_unknown():
    profile = get_profile("nonexistent")
    assert profile["document_id"] == "unknown"


def test_place_on_a4():
    img = Image.new("RGB", (800, 600), color=(200, 200, 200))
    profile = get_profile("aadhaar")
    result = place_on_a4(img, profile)
    assert result.size == (2480, 3508)


def test_place_on_a4_grayscale():
    img = Image.new("L", (800, 600), color=128)
    profile = get_profile("pan")
    result = place_on_a4(img, profile)
    assert result.size == (2480, 3508)
    assert result.mode == "L"
