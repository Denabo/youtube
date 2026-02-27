"""
Конфигурация проекта для пакетной обработки YouTube Shorts
"""
import os

# === БАЗОВЫЕ ПУТИ ===
BASE_DIR = r"C:\Users\hhdjd\PycharmProject\youtue"

# Входные папки
INPUT_CLIPS_DIR = os.path.join(BASE_DIR, "input", "clips")
INPUT_MUSIC_DIR = os.path.join(BASE_DIR, "input", "music")
INPUT_BACKGROUNDS_DIR = os.path.join(BASE_DIR, "input", "backgrounds")
INPUT_BANNERS_DIR = os.path.join(BASE_DIR, "input", "banners")

# Выходные папки
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
PROCESSED_CLIPS_DIR = os.path.join(BASE_DIR, "processed")
TEMP_DIR = os.path.join(BASE_DIR, "temp")

# Создаём все необходимые папки
for directory in [INPUT_CLIPS_DIR, INPUT_MUSIC_DIR, INPUT_BACKGROUNDS_DIR,
                  INPUT_BANNERS_DIR, OUTPUT_DIR, PROCESSED_CLIPS_DIR, TEMP_DIR]:
    os.makedirs(directory, exist_ok=True)

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
FONT_SIZE = 60
SUBTITLE_WORDS_PER_PHRASE = 2
SUBTITLE_BG_COLOR = (0, 0, 0, 180)
SUBTITLE_TEXT_COLOR = "white"
SUBTITLE_PADDING = 20

# === ПАРАМЕТРЫ РАСПОЛОЖЕНИЯ ===
CLIP_VERTICAL_POSITION = 0.35  # Чуть выше центра

# === WHISPER ===
WHISPER_MODEL = "base"
WHISPER_LANGUAGE = "ru"

# === ТИПЫ ОБРАБОТКИ ===
PROCESSING_MODES = {
    "1": {
        "name": "Обрезка + Баннер без фона",
        "type": "crop_banner",      # ← Тип режима
        "crop": True,
        "banner": True,
        "background": None,
        "resize_clip": False
    },
    "2": {
        "name": "Майнкрафт фон + Уменьшенный клип",
        "type": "background_clip",  # ← Тип режима
        "crop": False,
        "banner": True,
        "background": "minecraft",
        "resize_clip": True
    },
    "3": {
        "name": "Круговая обрезка (TikTok)",
        "type": "circle_crop",      # ← Новый тип
        "crop": True,
        "banner": False,
        "background": None,
        "resize_clip": False,
        "circle_mask": True
    },
    "4": {
        "name": "Двойной экран (Реакция)",
        "type": "split_screen",     # ← Новый тип
        "crop": False,
        "banner": False,
        "background": "blur",
        "resize_clip": True,
        "split_position": "top"
    },
    "5": {
        "name": "Фон + Баннер + Клип (Всё вместе)",
        "type": "full_package",     # ← Новый тип
        "crop": False,
        "banner": True,
        "background": "minecraft",
        "resize_clip": True
    },
    "6": {
        "name": "🔧 УНИВЕРСАЛЬНЫЙ (настраиваемый)",
        "type": "universal",        # ← УНИВЕРСАЛЬНЫЙ РЕЖИМ
        "crop": False,              # ← Меняй здесь!
        "banner": True,             # ← Меняй здесь!
        "background": True,         # ← Меняй здесь!
        "resize_clip": True         # ← Меняй здесь!
    }
}

# === РЕНДЕР ===
RENDER_PRESET = "medium"  # ultrafast, fast, medium, slow
RENDER_BITRATE = "8000k"
RENDER_THREADS = 4