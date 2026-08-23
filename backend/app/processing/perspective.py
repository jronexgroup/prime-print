import cv2
import numpy as np
from PIL import Image


def four_point_transform(image: Image.Image, pts: np.ndarray) -> Image.Image:
    img_array = np.array(image)

    rect = pts.astype("float32")

    tl, tr, br, bl = rect

    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    max_width = max(int(width_a), int(width_b))

    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)
    max_height = max(int(height_a), int(height_b))

    dst = np.array(
        [
            [0, 0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1],
        ],
        dtype="float32",
    )

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img_array, M, (max_width, max_height))

    return Image.fromarray(warped)


def correct_perspective(image: Image.Image, points: np.ndarray | None) -> Image.Image:
    if points is None:
        return image
    return four_point_transform(image, points)
