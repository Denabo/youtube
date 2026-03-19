"""
Модуль для удаления розового/маджента фона (хромакей)
"""
import numpy as np
from scipy.ndimage import gaussian_filter
from config import CHROMA_COLOR, CHROMA_TOLERANCE, CHROMA_EDGE_BLUR


# Розовый/маджента цвет по умолчанию — переопредели в config.py:
# CHROMA_COLOR = [255, 0, 255]
# CHROMA_TOLERANCE = 80
# CHROMA_EDGE_BLUR = 1.0

def chroma_key(clip, color=None, tolerance=None, edge_blur=None):
    """
    Удаление розового/маджента фона с чистой прозрачностью

    Args:
        clip: VideoFileClip объект
        color: RGB цвет для удаления (по умолчанию маджента [255, 0, 255])
        tolerance: Толерантность удаления
        edge_blur: Размытие краёв маски

    Returns:
        VideoFileClip с прозрачным фоном
    """
    if color is None:
        color = CHROMA_COLOR  # должен быть [255, 0, 255] или близкий
    if tolerance is None:
        tolerance = CHROMA_TOLERANCE
    if edge_blur is None:
        edge_blur = CHROMA_EDGE_BLUR

    def make_mask(frame):
        """Создаёт маску прозрачности для кадра"""
        frame_float = frame.astype(np.float32)
        color_array = np.array(color, dtype=np.float32)

        # Евклидово расстояние до целевого цвета
        diff = np.sqrt(np.sum((frame_float - color_array) ** 2, axis=2))
        mask = np.clip((diff - tolerance / 3) / (tolerance / 3), 0, 1)

        r = frame_float[:, :, 0]
        g = frame_float[:, :, 1]
        b = frame_float[:, :, 2]

        # Маджента: высокий R и B, низкий G
        magenta_dominance = (r > g * 1.2) & (b > g * 1.2) & (r > 150) & (b > 100)
        mask[magenta_dominance] = 0

        # Дополнительное подавление по пурпурному оттенку
        # Пурпурность = среднее R и B минус G
        magenta_tint = (r + b) / 2 - g
        high_magenta = magenta_tint > 40
        mask[high_magenta] *= np.clip(1 - (magenta_tint[high_magenta] / 150), 0, 1)

        # Размытие краёв для плавности
        if edge_blur > 0:
            mask = gaussian_filter(mask, sigma=edge_blur)

        # Бинаризация: убираем полупрозрачные артефакты
        mask = np.where(mask < 0.3, 0.0, mask)
        mask = np.where(mask > 0.7, 1.0, mask)

        return mask

    mask_clip = clip.fl_image(make_mask)
    mask_clip.ismask = True

    return clip.set_mask(mask_clip)