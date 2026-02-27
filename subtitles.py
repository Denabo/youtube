"""
Модуль для генерации и добавления субтитров
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
import whisper

from config import (
    WHISPER_MODEL, WHISPER_LANGUAGE,
    FONT_PATH, FONT_SIZE, SUBTITLE_WORDS_PER_PHRASE,
    SUBTITLE_BG_COLOR, SUBTITLE_TEXT_COLOR, SUBTITLE_PADDING
)


def generate_subtitles(video_path):
    """
    Распознаёт речь в видео и создаёт субтитры

    Args:
        video_path: путь к видео файлу

    Returns:
        list of tuples: [(start_time, end_time, text), ...]
    """
    try:
        video = VideoFileClip(video_path)
        temp_audio = "temp_audio_whisper.wav"

        # Извлекаем аудио
        video.audio.write_audiofile(
            temp_audio,
            fps=16000,
            codec="pcm_s16le",
            logger=None
        )
        video.close()

        # Загружаем модель Whisper
        model = whisper.load_model(WHISPER_MODEL)

        # Распознаём речь
        result = model.transcribe(
            temp_audio,
            language=WHISPER_LANGUAGE,
            verbose=False
        )

        # Формируем список субтитров
        subtitles = []
        for seg in result["segments"]:
            start = seg["start"]
            end = seg["end"]
            text = seg["text"].strip()
            if text:
                subtitles.append((start, end, text))

        # Удаляем временный файл
        if os.path.exists(temp_audio):
            os.remove(temp_audio)

        return subtitles

    except Exception as e:
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        raise


def add_stylish_subtitles(video, subtitles):
    """
    Добавляет стильные субтитры к видео

    Args:
        video: VideoFileClip объект
        subtitles: список субтитров от generate_subtitles()

    Returns:
        CompositeVideoClip с субтитрами
    """
    subtitle_clips = []

    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except:
        font = ImageFont.load_default()

    for start, end, text in subtitles:
        # Разбиваем текст на короткие фразы
        words = text.split()
        short_phrases = [
            " ".join(words[i:i + SUBTITLE_WORDS_PER_PHRASE])
            for i in range(0, len(words), SUBTITLE_WORDS_PER_PHRASE)
        ]

        phrase_duration = (end - start) / len(short_phrases)

        for i, phrase in enumerate(short_phrases):
            try:
                img = Image.new("RGBA", (video.w, video.h), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)

                bbox = draw.textbbox((0, 0), phrase, font=font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]

                x = (video.w - text_w) // 2
                y = (video.h - text_h) // 2

                draw.rectangle(
                    (
                        x - SUBTITLE_PADDING,
                        y - SUBTITLE_PADDING,
                        x + text_w + SUBTITLE_PADDING,
                        y + text_h + SUBTITLE_PADDING
                    ),
                    fill=SUBTITLE_BG_COLOR
                )

                draw.text((x, y), phrase, font=font, fill=SUBTITLE_TEXT_COLOR)

                phrase_start = start + i * phrase_duration
                txt_clip = (
                    ImageClip(np.array(img), duration=phrase_duration)
                    .set_start(phrase_start)
                    .set_position("center")
                )

                subtitle_clips.append(txt_clip)

            except:
                continue

    return CompositeVideoClip([video, *subtitle_clips])