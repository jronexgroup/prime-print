import cv2
import numpy as np
from PIL import Image


def enhance_for_print(image: Image.Image) -> Image.Image:
    img_array = np.array(image)

    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array

    # Gentle denoise
    denoised = cv2.fastNlMeansDenoising(gray, h=6)

    # Gentle CLAHE for contrast
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # Light sharpening
    kernel = np.array([[0, -0.5, 0], [-0.5, 3, -0.5], [0, -0.5, 0]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)

    # Gentle brightness correction
    mean_brightness = np.mean(sharpened)
    if mean_brightness < 100:
        # Very dark image — brighten gently
        alpha = 1.2
        beta = 25
        sharpened = cv2.convertScaleAbs(sharpened, alpha=alpha, beta=beta)
    elif mean_brightness > 220:
        # Too bright
        alpha = 0.9
        beta = -10
        sharpened = cv2.convertScaleAbs(sharpened, alpha=alpha, beta=beta)

    return Image.fromarray(sharpened)
