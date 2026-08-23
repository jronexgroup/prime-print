import re
from pathlib import Path
from typing import Tuple

import pytesseract
from PIL import Image

PROFILES_DIR = Path(__file__).parent.parent / "profiles"


def extract_text(image: Image.Image) -> str:
    try:
        text = pytesseract.image_to_string(image, lang="eng+hin")
        return text
    except Exception:
        return ""


def classify_document(image: Image.Image) -> Tuple[str, float]:
    text = extract_text(image)
    text_upper = text.upper()

    scores = {
        "aadhaar": 0.0,
        "pan": 0.0,
        "voter_id": 0.0,
    }

    aadhaar_keywords = ["AADHAAR", "आधार", "GOVERNMENT OF INDIA", "भारत सरकार"]
    for kw in aadhaar_keywords:
        if kw in text_upper or kw in text:
            scores["aadhaar"] += 0.3

    aadhaar_pattern = r"\d{4}\s?\d{4}\s?\d{4}"
    if re.search(aadhaar_pattern, text):
        scores["aadhaar"] += 0.2

    pan_keywords = ["INCOME TAX DEPARTMENT", "PERMANENT ACCOUNT NUMBER", "पैन"]
    for kw in pan_keywords:
        if kw in text_upper or kw in text:
            scores["pan"] += 0.3

    pan_pattern = r"[A-Z]{5}\d{4}[A-Z]"
    if re.search(pan_pattern, text):
        scores["pan"] += 0.3

    voter_keywords = ["ELECTION COMMISSION", "VOTER ID", "मतदाता पहचान", "EPIC"]
    for kw in voter_keywords:
        if kw in text_upper or kw in text:
            scores["voter_id"] += 0.3

    voter_pattern = r"[A-Z]{3}\d{7}"
    if re.search(voter_pattern, text):
        scores["voter_id"] += 0.2

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    if best_score < 0.3:
        return "unknown", 0.0

    confidence = min(best_score, 1.0)
    return best_type, confidence
