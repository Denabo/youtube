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
INPUT_FONTS_DIR = str(BASE_DIR / "input" / "fonts")

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
    INPUT_FONTS_DIR,
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

# === ПАРАМЕТРЫ ХРОМАКЕЯ ===
CHROMA_COLOR = (0, 255, 0)
CHROMA_TOLERANCE = 120
CHROMA_EDGE_BLUR = 1

# === ПАРАМЕТРЫ СУБТИТРОВ ===
FONT_PATH = "C:/Windows/Fonts/arialbd.ttf"
FONT_SIZE = 70
SUBTITLE_WORDS_PER_PHRASE = 1
SUBTITLE_BG_COLOR = (0, 0, 0, 0)
SUBTITLE_TEXT_COLOR = "#ffd400"
SUBTITLE_STROKE_COLOR = "black"
SUBTITLE_STROKE_WIDTH = 4
SUBTITLE_PADDING = 0
SUBTITLE_VERTICAL_OFFSET = 380  # Смещение суб3# титров: ~3/4 высоты для 1920px (можно менять)
SUBTITLE_RENDERER = "moviepy"

# ASS-стиль (если SUBTITLE_RENDERER = "ass")
ASS_FONT_NAME = "Arial Bold"
ASS_OUTLINE = 3
ASS_SHADOW = 1
ASS_ALIGNMENT = 2  # 2 = по центру снизу

# === ПАРАМЕТРЫ РАСПОЛОЖЕНИЯ ===
CLIP_VERTICAL_POSITION = 0.35  # Чуть выше центра
BANNER_VERTICAL_POSITION = -300  # Позиция баннера по вертикали (px, можно отрицательная)

# === WHISPER ===
WHISPER_MODEL = "base"
WHISPER_LANGUAGE = "ru"

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
    "5": {
        "name": "Субтитры + обрезка 9:16",
        "type": "subtitles_crop",
        "crop": True,
        "banner": False,
        "background": False,
        "resize_clip": False,
    },
    "6": {
        "name": "Зеркало: фон 0.90 + видео 1.05 + баннер",
        "type": "mirror_bg_and_clip",
        "crop": False,
        "banner": True,
        "background": True,
        "resize_clip": True,
        "mirror_clip": True,
        "clip_speed": 1.05,
        "mirror_background": True,
        "background_speed": 0.90,
    },
    "7": {
        "name": "Зеркало: только видео + баннер",
        "type": "mirror_clip_only",
        "crop": True,
        "banner": True,
        "background": False,
        "resize_clip": False,
        "mirror_clip": True,
    },
}

# === РЕНДЕР ===
RENDER_PRESET = "medium"
RENDER_BITRATE = "8000k"
RENDER_THREADS = 4
