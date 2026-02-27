import os
import time
import logging
import numpy as np
from moviepy.editor import (
    VideoFileClip,
    CompositeVideoClip,
    ImageClip,
    AudioFileClip,
    CompositeAudioClip
)
from PIL import Image, ImageDraw, ImageFont
import whisper


# === НАСТРОЙКА ЛОГГЕРА ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)


# === ПУТИ ===
INPUT_VIDEO = r"C:\Users\hhdjd\PycharmProject\youtue\input\Clips\clip.mp4"
BLURRED_BG = r"C:\Users\hhdjd\PycharmProject\youtue\input\backgraund\blurred_background.mp4"
BANNER_PATH = r"C:\Users\hhdjd\PycharmProject\youtue\input\banner\banner_fixed.mp4"
READY_BG = r"C:\Users\hhdjd\PycharmProject\youtue\input\backgraund\ready_background.mp4"
MUSIC_PATH = r"C:\Users\hhdjd\PycharmProject\youtue\input\music\music.mp3"
OUTPUT_VIDEO = r"C:\Users\hhdjd\PycharmProject\youtue\output\shorts_final.mp4"

# === ПАРАМЕТРЫ ===
shorts_w, shorts_h = 1080, 1920
music_volume = 0.2
voice_volume = 1.0


# === УТИЛИТА: замер времени ===
def step_timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        log.info(f"▶ {func.__name__.replace('_', ' ').capitalize()}...")
        result = func(*args, **kwargs)
        log.info(f"✅ {func.__name__} завершено за {time.time() - start:.2f} сек")
        return result
    return wrapper


# === ХРОМАКЕЙ ===
def chroma_key(clip, color=(0, 255, 0), tolerance=80):
    """Удаляет зелёный фон из видео"""
    def mask_color(frame):
        diff = np.sqrt(np.sum((frame - np.array(color)) ** 2, axis=2))
        mask = (diff > tolerance).astype(np.float32)
        return mask

    mask_clip = clip.fl_image(mask_color)
    mask_clip.ismask = True
    return clip.set_mask(mask_clip)


# === СОЗДАНИЕ ГОТОВОГО ФОНА ===
@step_timer
def prepare_background_with_banner():
    """Создаёт готовый фон с зацикленным баннером"""
    log.info("🧱 Создаём готовый фон с баннером...")
    try:
        bg = VideoFileClip(BLURRED_BG).without_audio()
        bg = bg.resize(height=shorts_h).crop(width=shorts_w, height=shorts_h, x_center=bg.w / 2, y_center=bg.h / 2)

        banner = None
        if os.path.exists(BANNER_PATH):
            try:
                banner = VideoFileClip(BANNER_PATH).without_audio()
                banner = chroma_key(banner)
                banner = banner.resize(width=int(shorts_w * 0.9))
                banner = banner.set_position(("center", shorts_h * 0.05))

                # ⏩ зацикливаем баннер под длину фона
                if banner.duration < bg.duration:
                    log.info(f"🔁 Баннер короче ({banner.duration:.1f}с), зацикливаем до {bg.duration:.1f}с...")
                    banner = banner.loop(duration=bg.duration)
                else:
                    banner = banner.subclip(0, bg.duration)
            except Exception as e:
                log.warning(f"⚠️ Баннер повреждён или не читается: {e}")
                banner = None
        else:
            log.warning("⚠️ Баннер не найден, продолжаем без него.")

        clips = [bg]
        if banner:
            clips.append(banner)

        final_bg = CompositeVideoClip(clips, size=(shorts_w, shorts_h))
        final_bg.write_videofile(
            READY_BG,
            codec="libx264",
            audio=False,
            fps=30,
            threads=4,
        )
        log.info(f"✅ Готовый фон сохранён в {READY_BG}")

    except Exception as e:
        log.error(f"❌ Ошибка при сборке фона: {e}")

# === РАСПОЗНАВАНИЕ РЕЧИ ===
@step_timer
def generate_subtitles(video_path, model_name="base"):
    from moviepy.editor import VideoFileClip
    log.info("🎬 Извлекаем аудио из видео...")
    video = VideoFileClip(video_path)
    temp_audio = "temp_audio.wav"
    video.audio.write_audiofile(temp_audio, fps=16000, codec="pcm_s16le")

    log.info("🧠 Загружаем модель Whisper...")
    model = whisper.load_model(model_name)

    log.info("🔍 Распознаём речь...")
    result = model.transcribe(temp_audio, language='ru')

    subtitles = [(seg["start"], seg["end"], seg["text"].strip()) for seg in result["segments"]]
    os.remove(temp_audio)
    return subtitles


# === СУБТИТРЫ ===
@step_timer
def add_stylish_subtitles(video, subtitles, font_path="C:/Windows/Fonts/arialbd.ttf"):
    log.info("💬 Добавляем субтитры...")
    clips = []

    for start, end, text in subtitles:
        words = text.split()
        short_phrases = [" ".join(words[i:i + 2]) for i in range(0, len(words), 2)]
        phrase_duration = (end - start) / len(short_phrases)

        for i, phrase in enumerate(short_phrases):
            font = ImageFont.truetype(font_path, 60)
            img = Image.new("RGBA", (video.w, video.h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            bbox = draw.textbbox((0, 0), phrase, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = (video.w - w) // 2
            y = (video.h - h) // 2
            draw.rectangle((x - 20, y - 20, x + w + 20, y + h + 20), fill=(0, 0, 0, 150))
            draw.text((x, y), phrase, font=font, fill="white")

            txt_clip = (ImageClip(np.array(img), duration=phrase_duration)
                        .set_start(start + i * phrase_duration)
                        .set_position("center"))
            clips.append(txt_clip)

    return CompositeVideoClip([video, *clips])


# === СБОРКА ФИНАЛЬНОГО ВИДЕО ===
@step_timer
def create_final_video():
    log.info("🚀 Загружаем клипы и фон...")
    try:
        main_video = VideoFileClip(INPUT_VIDEO)
        background = VideoFileClip(READY_BG).without_audio()
    except Exception as e:
        log.error(f"Ошибка загрузки видео: {e}")
        return

    try:
        main_resized = main_video.resize(width=shorts_w)
        if main_resized.h > shorts_h:
            main_resized = main_resized.resize(height=shorts_h)

        y = (shorts_h / 2) - main_resized.h
        y = max(y, -shorts_h * 0.25)
        main_resized = main_resized.set_position(("center", y))

        layers = [background, main_resized]
        base_video = CompositeVideoClip(layers, size=(shorts_w, shorts_h))
        base_video = base_video.set_audio(main_resized.audio.volumex(voice_volume))

        log.info("🎵 Добавляем музыку...")
        music = AudioFileClip(MUSIC_PATH).volumex(music_volume)
        music = music.audio_loop(duration=base_video.duration)
        mixed_audio = CompositeAudioClip([base_video.audio, music])
        base_video = base_video.set_audio(mixed_audio)

        subtitles = generate_subtitles(INPUT_VIDEO)
        final = add_stylish_subtitles(base_video, subtitles)

        log.info("💾 Рендерим финальное видео...")
        final.write_videofile(
            OUTPUT_VIDEO,
            codec="libx264",
            audio_codec="aac",
            fps=30,
            threads=4
        )

        log.info(f"✅ Готово! Видео сохранено в: {OUTPUT_VIDEO}")

    except Exception as e:
        log.error(f"Ошибка при создании видео: {e}")


# === ГЛАВНЫЙ ЗАПУСК ===
if __name__ == "__main__":
    log.info("🎬 Старт проекта видео-сборки")

    if not os.path.exists(READY_BG):
        prepare_background_with_banner()
    else:
        log.info("🔹 Используем готовый фон")

    create_final_video()

    log.info("🏁 Все процессы завершены успешно.")
