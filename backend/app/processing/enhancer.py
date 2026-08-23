import cv2
import numpy as np
from PIL import Image, ImageEnhance


def enhance_for_print(image: Image.Image) -> Image.Image:
    img_array = np.array(image)

    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    denoised = cv2.fastNlMeansDenoising(enhanced, h=10)

    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened = cv2.filter2D(denoised, -1, kernel)

    mean_brightness = np.mean(sharpened)
    if mean_brightness < 120:
        alpha = 1.3
        beta = 20
        sharpened = cv2.convertScaleAbs(sharpened, alpha=alpha, beta=beta)
    elif mean_brightness > 200:
        alpha = 0.9
        beta = -10
        sharpened = cv2.convertScaleAbs(sharpened, alpha=alpha, beta=beta)

    _, binary = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    white_ratio = np.sum(binary == 255) / binary.size
    if white_ratio > 0.85:
        result = binary
    else:
        result = sharpened

    return Image.fromarray(result)
