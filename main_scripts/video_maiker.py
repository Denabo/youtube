import cv2
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
import os


# === ПУТИ ===
INPUT_VIDEO = r"C:\Users\hhdjd\PycharmProject\youtue\input\Clips\clip.mp4"
BLURRED_BG = r"C:\Users\hhdjd\PycharmProject\youtue\input\backgraund\blurred_background.mp4"
BANNER_PATH = r"C:\Users\hhdjd\PycharmProject\youtue\input\banner\banner_fixed.mp4"# зелёный фон
MUSIC_PATH = r"C:\Users\hhdjd\PycharmProject\youtue\input\music\music.mp3"
OUTPUT_VIDEO = r"C:\Users\hhdjd\PycharmProject\youtue\output\shorts_final.mp4"

# === ПАРАМЕТРЫ ===
music_volume = 0.2     # громкость фоновой музыки
voice_volume = 1.0     # громкость речи
shorts_w, shorts_h = 1080, 1920


# === ФУНКЦИЯ: распознавание речи ===
def generate_subtitles(video_path, model_name="base"):
    print("🎬 Извлекаем аудио из видео...")
    video = VideoFileClip(video_path)
    temp_audio = "temp_audio.wav"
    video.audio.write_audiofile(temp_audio, fps=16000, codec="pcm_s16le")

    print("🧠 Загружаем модель Whisper...")
    model = whisper.load_model(model_name)

    print("🔍 Распознаём речь...")
    result = model.transcribe(temp_audio, language='ru')

    subtitles = [(seg["start"], seg["end"], seg["text"].strip()) for seg in result["segments"]]

    os.remove(temp_audio)
    return subtitles


# === ФУНКЦИЯ: стильные субтитры ===
def add_stylish_subtitles(video, subtitles, font_path="C:/Windows/Fonts/arialbd.ttf"):
    print("💬 Добавляем субтитры...")
    clips = []

    for start, end, text in subtitles:
        words = text.split()
        short_phrases = [" ".join(words[i:i + 2]) for i in range(0, len(words), 2)]
        phrase_duration = (end - start) / len(short_phrases)

        for i, phrase in enumerate(short_phrases):
            font_size = 60
            font = ImageFont.truetype(font_path, font_size)

            img = Image.new("RGBA", (video.w, video.h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            bbox = draw.textbbox((0, 0), phrase, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = (video.w - w) // 2
            y = (video.h - h) // 2

            bg_margin = 20
            draw.rectangle(
                (x - bg_margin, y - bg_margin, x + w + bg_margin, y + h + bg_margin),
                fill=(0, 0, 0, 150)
            )
            draw.text((x, y), phrase, font=font, fill="white")

            img_np = np.array(img)
            txt_clip = (ImageClip(img_np, duration=phrase_duration)
                        .set_start(start + i * phrase_duration)
                        .set_position("center"))
            clips.append(txt_clip)

    return CompositeVideoClip([video, *clips])


# === ФУНКЦИЯ: хромакей баннера ===
def chroma_key(clip, color=(0, 255, 0), tolerance=80):
    """Удаляет зелёный фон из видео"""
    def mask_color(frame):
        diff = np.sqrt(np.sum((frame - np.array(color)) ** 2, axis=2))
        mask = (diff > tolerance).astype(np.float32)
        return mask  # 1 — видно, 0 — прозрачное

    mask_clip = clip.fl_image(mask_color)
    mask_clip.ismask = True
    return clip.set_mask(mask_clip)


# === ФУНКЦИЯ: добавление баннера ===
def add_banner(main_duration):
    """Добавляет баннер, зацикливая его при необходимости"""
    if not os.path.exists(BANNER_PATH):
        print("⚠️ Баннер не найден, пропускаем.")
        return None

    print("🟩 Добавляем баннер (с зацикливанием)...")
    try:
        banner = VideoFileClip(BANNER_PATH).without_audio()
    except Exception as e:
        print(f"❌ Ошибка при загрузке баннера: {e}")
        return None

    try:
        banner = chroma_key(banner)
        banner = banner.resize(width=int(shorts_w * 0.9))
        banner = banner.set_position(("center", shorts_h * 0.05))

        # если баннер короче — зацикливаем до длины видео
        if banner.duration < main_duration:
            banner = banner.loop(duration=main_duration)
        else:
            banner = banner.subclip(0, main_duration)

        return banner

    except Exception as e:
        print(f"❌ Ошибка при обработке баннера: {e}")
        return None

# === ФУНКЦИЯ: сборка финального видео ===
def create_final_video():
    print("🚀 Загружаем клипы и фон...")
    main_video = VideoFileClip(INPUT_VIDEO)
    background = VideoFileClip(BLURRED_BG).without_audio()

    # подгоняем фон под вертикальный формат
    bg_ratio = background.w / background.h
    target_ratio = shorts_w / shorts_h
    if bg_ratio > target_ratio:
        background = background.resize(height=shorts_h)
    else:
        background = background.resize(width=shorts_w)
    background = background.crop(width=shorts_w, height=shorts_h,
                                 x_center=background.w / 2, y_center=background.h / 2)
    background = background.loop(duration=main_video.duration)

    # позиционируем основное видео (нижняя граница по центру)
    main_resized = main_video.resize(width=shorts_w)
    if main_resized.h > shorts_h:
        main_resized = main_resized.resize(height=shorts_h)

    y = (shorts_h / 2) - main_resized.h
    min_y = -shorts_h * 0.25
    if y < min_y:
        y = min_y
    main_resized = main_resized.set_position(("center", y))

    # добавляем баннер
    banner = add_banner(main_video.duration)

    # собираем видео без субтитров
    layers = [background, main_resized]
    if banner:
        layers.append(banner)
    base_video = CompositeVideoClip(layers, size=(shorts_w, shorts_h))
    base_video = base_video.set_audio(main_resized.audio.volumex(voice_volume))

    # === добавляем музыку ===
    print("🎵 Добавляем музыку...")
    music = AudioFileClip(MUSIC_PATH).volumex(music_volume)
    music = music.audio_loop(duration=base_video.duration)

    mixed_audio = CompositeAudioClip([base_video.audio, music])
    base_video = base_video.set_audio(mixed_audio)

    # === добавляем субтитры ===
    subtitles = generate_subtitles(INPUT_VIDEO)
    final = add_stylish_subtitles(base_video, subtitles)

    # === финальный рендер ===
    print("💾 Рендерим финальное видео...")
    final.write_videofile(
        OUTPUT_VIDEO,
        codec="libx264",
        audio_codec="aac",
        fps=30,
        threads=4
    )

    print(f"✅ Готово! Видео сохранено в: {OUTPUT_VIDEO}")


# === ЗАПУСК ===
if __name__ == "__main__":
    create_final_video()
