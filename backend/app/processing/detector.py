import cv2
import numpy as np
from PIL import Image


def order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    d = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(d)]
    rect[3] = pts[np.argmax(d)]
    return rect


def _find_largest_rectangle(gray: np.ndarray):
    h, w = gray.shape[:2]
    image_area = h * w

    # Adaptive threshold to handle varying lighting
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 10
    )

    # Also try Otsu
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Combine both
    combined = cv2.bitwise_or(binary, otsu)

    # Morphological close to connect text regions
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    closed = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Find contours on multiple versions
    for img_version in [closed, combined, binary]:
        contours, _ = cv2.findContours(img_version, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        for contour in contours[:15]:
            area = cv2.contourArea(contour)
            if area < image_area * 0.2:
                continue

            peri = cv2.arcLength(contour, True)
            for eps in [0.01, 0.02, 0.03, 0.04, 0.05]:
                approx = cv2.approxPolyDP(contour, eps * peri, True)
                if len(approx) == 4:
                    pts = approx.reshape(4, 2).astype("float32")
                    # Validate: check if it's roughly rectangular
                    ordered = order_points(pts)
                    w_actual = np.linalg.norm(ordered[1] - ordered[0])
                    h_actual = np.linalg.norm(ordered[3] - ordered[0])
                    if w_actual > 100 and h_actual > 100:
                        return ordered

    return None


def detect_document(image: Image.Image) -> np.ndarray | None:
    img_array = np.array(image)
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array

    points = _find_largest_rectangle(gray)

    if points is None:
        # Fallback: 5% margin from edges
        h, w = gray.shape[:2]
        mx, my = int(w * 0.05), int(h * 0.05)
        points = np.array([
            [mx, my], [w - mx, my],
            [w - mx, h - my], [mx, h - my],
        ], dtype="float32")

    return points


def crop_to_document(image: Image.Image, points: np.ndarray) -> Image.Image:
    if points is None:
        return image

    img_array = np.array(image)
    x_min = max(0, int(points[:, 0].min()))
    y_min = max(0, int(points[:, 1].min()))
    x_max = min(img_array.shape[1], int(points[:, 0].max()))
    y_max = min(img_array.shape[0], int(points[:, 1].max()))

    if x_max <= x_min + 10 or y_max <= y_min + 10:
        return image

    cropped = img_array[y_min:y_max, x_min:x_max]
    return Image.fromarray(cropped)
