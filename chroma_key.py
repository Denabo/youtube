"""
Модуль для удаления зелёного фона (хромакей)
"""
import numpy as np
from scipy.ndimage import gaussian_filter
from config import CHROMA_COLOR, CHROMA_TOLERANCE, CHROMA_EDGE_BLUR


def chroma_key(clip, color=None, tolerance=None, edge_blur=None):
    """
    Агрессивное удаление зелёного фона с чистой прозрачностью

    Args:
        clip: VideoFileClip объект
        color: RGB цвет для удаления
        tolerance: Толерантность удаления
        edge_blur: Размытие краёв маски

    Returns:
        VideoFileClip с полностью прозрачным фоном
    """
    if color is None:
        color = CHROMA_COLOR
    if tolerance is None:
        tolerance = CHROMA_TOLERANCE
    if edge_blur is None:
        edge_blur = CHROMA_EDGE_BLUR

    def make_mask(frame):
        """Создаёт маску прозрачности для кадра"""
        frame_float = frame.astype(np.float32)
        color_array = np.array(color, dtype=np.float32)

        diff = np.sqrt(np.sum((frame_float - color_array) ** 2, axis=2))
        mask = np.clip((diff - tolerance/3) / (tolerance/3), 0, 1)

        green_channel = frame_float[:, :, 1]
        red_channel = frame_float[:, :, 0]
        blue_channel = frame_float[:, :, 2]

        green_dominance = (green_channel > red_channel * 1.1) & (green_channel > blue_channel * 1.1)
        mask[green_dominance] = 0

        green_tint = green_channel - (red_channel + blue_channel) / 2
        high_green = green_tint > 20
        mask[high_green] *= np.clip(1 - (green_tint[high_green] / 100), 0, 1)

        if edge_blur > 0:
            mask = gaussian_filter(mask, sigma=edge_blur)

        mask = np.where(mask < 0.3, 0, mask)
        mask = np.where(mask > 0.7, 1, mask)

        return mask

    mask_clip = clip.fl_image(make_mask)
    mask_clip.ismask = True

    return clip.set_mask(mask_clip)