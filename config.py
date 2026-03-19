"""
Конфигурация проекта для пакетной обработки YouTube Shorts / Reels / Clips
"""
import os
from pathlib import Path

# === БАЗОВЫЕ ПУТИ ===
BASE_DIR = Path(__file__).resolve().parent

# Входные папки
INPUT_CLIPS_DIR = str(BASE_DIR / "input" / "clips")
INPUT_MUSIC_DIR = str(BASE_DIR / "input" / "music")
INPUT_BACKGROUNDS_DIR = str(BASE_DIR / "input" / "backgrounds")
INPUT_BANNERS_DIR = str(BASE_DIR / "input" / "banners")

# Выходные папки
OUTPUT_DIR = str(BASE_DIR / "output")
PROCESSED_CLIPS_DIR = str(BASE_DIR / "processed")
TEMP_DIR = str(BASE_DIR / "temp")

# Создаём все необходимые папки
for directory in [
    INPUT_CLIPS_DIR,
    INPUT_MUSIC_DIR,
    INPUT_BACKGROUNDS_DIR,
    INPUT_BANNERS_DIR,
    OUTPUT_DIR,
    PROCESSED_CLIPS_DIR,
    TEMP_DIR,
]:
    os.makedirs(directory, exist_ok=True)

# === ПЛАТФОРМЫ ===
PLATFORM_PROFILES = {
    "youtube": {"name": "YouTube Shorts", "width": 1080, "height": 1920, "fps": 30},
    "tiktok": {"name": "TikTok", "width": 1080, "height": 1920, "fps": 30},
    "instagram": {"name": "Instagram Reels", "width": 1080, "height": 1920, "fps": 30},
    "vk": {"name": "VK Клипы", "width": 1080, "height": 1920, "fps": 30},
}
DEFAULT_PLATFORMS = ["youtube", "tiktok", "instagram", "vk"]

# === ПАРАМЕТРЫ ВИДЕО ===
SHORTS_WIDTH = 1080
SHORTS_HEIGHT = 1920
FPS = 30

# === ПАРАМЕТРЫ АУДИО ===
DEFAULT_MUSIC_VOLUME = 0.2
VOICE_VOLUME = 1.0

# === ПАРАМЕТРЫ ХРОМАКЕЯ (розовый/маджента) ===
CHROMA_COLOR = (255, 0, 255)
CHROMA_TOLERANCE = 120
CHROMA_EDGE_BLUR = 1

# === ПАРАМЕТРЫ СУБТИТРОВ ===
FONT_PATH = "C:/Windows/Fonts/arialbd.ttf"
FONT_SIZE = 60
SUBTITLE_WORDS_PER_PHRASE = 2
SUBTITLE_BG_COLOR = (0, 0, 0, 180)
SUBTITLE_TEXT_COLOR = "white"
SUBTITLE_PADDING = 20
SUBTITLE_BOTTOM_MARGIN = 140

# === ПАРАМЕТРЫ РАСПОЛОЖЕНИЯ ===
CLIP_VERTICAL_POSITION = 0.35  # Чуть выше центра
BANNER_TOP_MARGIN = 0
BANNER_VERTICAL_OFFSET = 0  # может быть отрицательным или большим, чем высота кадра

# === WHISPER ===
WHISPER_MODEL = "base"
WHISPER_LANGUAGE = None  # None = автоопределение языка

# === ТИПЫ ОБРАБОТКИ ===
PROCESSING_MODES = {
    "1": {
        "name": "Обрезка + Баннер без фона",
        "type": "crop_banner",
        "crop": True,
        "banner": True,
        "background": False,
        "resize_clip": False,
    },
    "2": {
        "name": "Фон + Уменьшенный клип + Баннер",
        "type": "background_clip",
        "crop": False,
        "banner": True,
        "background": True,
        "resize_clip": True,
    },
    "3": {
        "name": "Только обрезка 9:16",
        "type": "crop_only",
        "crop": True,
        "banner": False,
        "background": False,
        "resize_clip": False,
    },
    "4": {
        "name": "Универсальный (редактируется в config.py)",
        "type": "universal",
        "crop": False,
        "banner": True,
        "background": True,
        "resize_clip": True,
    },
}

# === РЕНДЕР ===
RENDER_PRESET = "medium"
RENDER_BITRATE = "8000k"
RENDER_THREADS = 4
