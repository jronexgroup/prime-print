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


def detect_document(image: Image.Image) -> np.ndarray | None:
    img_array = np.array(image)
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges = cv2.dilate(edges, kernel, iterations=2)
    edges = cv2.erode(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    image_area = gray.shape[0] * gray.shape[1]
    min_area = image_area * 0.1

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

        if len(approx) == 4:
            pts = approx.reshape(4, 2).astype("float32")
            return order_points(pts)

    return None


def crop_to_document(image: Image.Image, points: np.ndarray) -> Image.Image:
    if points is None:
        return image

    img_array = np.array(image)
    x_min = max(0, int(points[:, 0].min()))
    y_min = max(0, int(points[:, 1].min()))
    x_max = min(img_array.shape[1], int(points[:, 0].max()))
    y_max = min(img_array.shape[0], int(points[:, 1].max()))

    cropped = img_array[y_min:y_max, x_min:x_max]
    return Image.fromarray(cropped)
