"""
Модуль для генерации и добавления субтитров
"""
import os
import re
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
import whisper

from config import (
    WHISPER_MODEL, WHISPER_LANGUAGE,
    FONT_PATH, FONT_SIZE, SUBTITLE_WORDS_PER_PHRASE,
    SUBTITLE_BG_COLOR, SUBTITLE_TEXT_COLOR, SUBTITLE_PADDING,
    SUBTITLE_VERTICAL_OFFSET,
    ASS_FONT_NAME, ASS_OUTLINE, ASS_SHADOW, ASS_ALIGNMENT
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
                y = (video.h - text_h) // 2 + SUBTITLE_VERTICAL_OFFSET

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


def _seconds_to_ass_time(seconds):
    """Преобразует секунды в формат времени ASS: H:MM:SS.cc"""
    total_cs = max(0, int(round(seconds * 100)))
    cs = total_cs % 100
    total_s = total_cs // 100
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _ass_escape_text(text):
    """Экранирует спецсимволы для ASS/SSA диалогов."""
    text = re.sub(r"[\r\n]+", " ", text.strip())
    text = text.replace("{", r"\{").replace("}", r"\}")
    return text


def create_ass_subtitles_file(subtitles, video_height, ass_path):
    """
    Создаёт stylized .ass файл из распознанных субтитров.

    Args:
        subtitles: [(start, end, text), ...]
        video_height: высота видео (для расчёта нижнего отступа)
        ass_path: путь сохранения .ass
    """
    margin_v = max(0, int(video_height / 2 - SUBTITLE_VERTICAL_OFFSET))

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{ASS_FONT_NAME},{FONT_SIZE},&H00FFFFFF,&H0000FFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,{ASS_OUTLINE},{ASS_SHADOW},{ASS_ALIGNMENT},30,30,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines = [header]
    for start, end, text in subtitles:
        if not text.strip():
            continue
        start_ts = _seconds_to_ass_time(start)
        end_ts = _seconds_to_ass_time(end)
        safe_text = _ass_escape_text(text)
        lines.append(f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{safe_text}\n")

    with open(ass_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return ass_path


def burn_ass_subtitles(input_video_path, ass_path, output_video_path):
    """
    Вжигает ASS-субтитры в видео через ffmpeg.
    """
    command = [
        "ffmpeg",
        "-y",
        "-i", input_video_path,
        "-vf", f"subtitles={ass_path}",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "copy",
        output_video_path,
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
