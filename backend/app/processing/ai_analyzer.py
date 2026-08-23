import base64
import json
import os

import httpx
from dotenv import load_dotenv
from PIL import Image

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


NIM_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NIM_API_KEY = os.getenv("NIM_API_KEY", "")
VISION_MODEL = "meta/llama-3.2-11b-vision-instruct"

VISION_PROMPT = """You are a document processing AI. Analyze this photograph of a document.

TASK: Find the exact document boundaries and return processing instructions.

The document is somewhere in this photo. There may be a table, wall, shadows, or other background around it.

Return ONLY valid JSON (no markdown, no extra text):
{
  "document_type": "aadhaar|pan|voter_id|driving_license|passport|certificate|unknown",
  "crop": {
    "top_left_x": 0.15,
    "top_left_y": 0.10,
    "bottom_right_x": 0.85,
    "bottom_right_y": 0.90
  },
  "rotation_degrees": 2.5,
  "brightness_adjustment": 15,
  "contrast_adjustment": 10,
  "is_document_visible": true,
  "confidence": 0.85,
  "notes": "document is slightly tilted clockwise"
}

FIELD RULES:

document_type:
- "aadhaar": Indian Aadhaar card (has "आधार" or "AADHAAR" text, 12-digit number)
- "pan": PAN card (has "INCOME TAX" or alphanumeric PAN format)
- "voter_id": Voter ID / EPIC card
- "driving_license": Driving license
- "passport": Passport
- "certificate": Any certificate or document
- "unknown": Cannot determine

crop (CRITICAL - be precise):
- Coordinates are NORMALIZED (0.0 = image edge, 1.0 = opposite edge)
- Find the EXACT corners of the document
- Exclude table, wall, shadows, any background
- The document is usually a rectangle in the center or offset area
- Look for sharp edges where document meets background
- Example: if document starts 20% from left edge, set top_left_x = 0.20

rotation_degrees:
- Estimate the angle the document is tilted
- Positive = clockwise rotation needed to straighten
- Negative = counter-clockwise
- Use small values: 0.5 to 5.0 for typical photos

brightness_adjustment:
- Range: -50 to 50
- If image is dark, use positive (10 to 30)
- If image is overexposed, use negative (-10 to -30)
- 0 = no change

contrast_adjustment:
- Range: -50 to 50
- If image looks flat/washed out, use positive (10 to 25)
- If too harsh, use negative
- 0 = no change

is_document_visible:
- true if you can clearly see a document
- false if it's just a random photo with no document

confidence:
- How sure you are about your analysis (0.0 to 1.0)

Return ONLY the JSON object. No explanation, no markdown."""


def analyze_image(image_path: str) -> dict:
    img = Image.open(image_path)

    max_dim = 1024
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    import io
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    img_b64 = base64.b64encode(buffer.getvalue()).decode()

    headers = {
        "Authorization": f"Bearer {NIM_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": VISION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": VISION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                    },
                ],
            }
        ],
        "max_tokens": 1024,
        "temperature": 0.1,
    }

    try:
        resp = httpx.post(NIM_API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        content = data["choices"][0]["message"]["content"]

        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

        result = json.loads(content)

        # Validate and clamp values
        crop = result.get("crop", {})
        crop["top_left_x"] = max(0.0, min(1.0, crop.get("top_left_x", 0.05)))
        crop["top_left_y"] = max(0.0, min(1.0, crop.get("top_left_y", 0.05)))
        crop["bottom_right_x"] = max(0.0, min(1.0, crop.get("bottom_right_x", 0.95)))
        crop["bottom_right_y"] = max(0.0, min(1.0, crop.get("bottom_right_y", 0.95)))
        result["crop"] = crop

        result["rotation_degrees"] = max(-45.0, min(45.0, result.get("rotation_degrees", 0)))
        result["brightness_adjustment"] = max(-50, min(50, result.get("brightness_adjustment", 0)))
        result["contrast_adjustment"] = max(-50, min(50, result.get("contrast_adjustment", 0)))
        result["confidence"] = max(0.0, min(1.0, result.get("confidence", 0)))

        return result

    except httpx.HTTPStatusError as e:
        print(f"[AI] API error: {e.response.status_code}")
        return _fallback()
    except json.JSONDecodeError:
        print(f"[AI] Parse error: {content[:300]}")
        return _fallback()
    except Exception as e:
        print(f"[AI] Error: {e}")
        return _fallback()


def _fallback() -> dict:
    return {
        "document_type": "unknown",
        "crop": {"top_left_x": 0.05, "top_left_y": 0.05, "bottom_right_x": 0.95, "bottom_right_y": 0.95},
        "rotation_degrees": 0,
        "brightness_adjustment": 0,
        "contrast_adjustment": 0,
        "is_document_visible": False,
        "confidence": 0.0,
        "notes": "AI unavailable",
    }
