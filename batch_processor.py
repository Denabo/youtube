"""
Пакетная обработка видео с очередью и поддержкой нескольких платформ
"""
import os
import shutil
from pathlib import Path

from moviepy.editor import VideoFileClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip

from config import (
    CLIP_VERTICAL_POSITION,
    DEFAULT_MUSIC_VOLUME,
    DEFAULT_PLATFORMS,
    INPUT_BACKGROUNDS_DIR,
    INPUT_BANNERS_DIR,
    INPUT_CLIPS_DIR,
    INPUT_MUSIC_DIR,
    OUTPUT_DIR,
    PLATFORM_PROFILES,
    PROCESSING_MODES,
    PROCESSED_CLIPS_DIR,
    RENDER_BITRATE,
    RENDER_PRESET,
    RENDER_THREADS,
    SHORTS_HEIGHT,
    SHORTS_WIDTH,
    VOICE_VOLUME,
)
from chroma_key import chroma_key
from subtitles import generate_subtitles, add_stylish_subtitles


class VideoProcessor:
    """Класс для обработки одного видео"""

    def __init__(self, clip_path, music_path=None, mode="1"):
        self.clip_path = clip_path
        self.music_path = music_path
        self.mode = PROCESSING_MODES.get(mode, PROCESSING_MODES["1"])
        self.clip_name = Path(clip_path).stem
        self.frame_w = SHORTS_WIDTH
        self.frame_h = SHORTS_HEIGHT

    def process(self, output_path, platform_key, subtitles=None):
        """Главная функция обработки видео"""
        profile = PLATFORM_PROFILES[platform_key]
        self.frame_w = profile["width"]
        self.frame_h = profile["height"]

        print(f"⚙️  Обработка: {self.clip_name} -> {profile['name']}")
        clip = VideoFileClip(self.clip_path)

        video = self._mode_universal(clip)

        if self.music_path and os.path.exists(self.music_path):
            video = self._add_music(video)

        if subtitles:
            print("   💬 Наложение субтитров...")
            video = add_stylish_subtitles(video, subtitles)

        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        print("   💾 Рендер видео...")
        video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=profile["fps"],
            threads=RENDER_THREADS,
            preset=RENDER_PRESET,
            bitrate=RENDER_BITRATE,
            logger=None,
        )

        clip.close()
        video.close()
        print(f"   ✅ Готово: {Path(output_path).name}\n")

    def _fit_background(self, bg, duration):
        bg = bg.resize(height=self.frame_h)
        if bg.w > self.frame_w:
            x_center = bg.w / 2
            bg = bg.crop(
                x1=x_center - self.frame_w / 2,
                y1=0,
                x2=x_center + self.frame_w / 2,
                y2=self.frame_h,
            )
        if bg.duration < duration:
            bg = bg.loop(duration=duration)
        else:
            bg = bg.subclip(0, duration)
        return bg

    def _open_first_valid_clip(self, files, label):
        """Открывает первый корректный видеофайл из списка."""
        for candidate in files:
            try:
                opened = VideoFileClip(str(candidate)).without_audio()
                return opened, candidate
            except Exception as err:
                print(f"   ⚠️  {label}: не удалось открыть {candidate.name} ({err})")
        return None, None

    def _mode_universal(self, clip):
        """Универсальная сборка: фон/обрезка/уменьшение/баннер"""
        print(f"   🎬 Режим: {self.mode['name']}")
        layers = []
        clip_to_use = clip

        if self.mode.get("background"):
            bg_files = list(Path(INPUT_BACKGROUNDS_DIR).glob("*.mp4"))
            if bg_files:
                bg, bg_path = self._open_first_valid_clip(bg_files, "Фон")
                if bg is not None:
                    print(f"   🖼️  Фон: {bg_path.name}")
                    bg = self._fit_background(bg, clip.duration)
                    layers.append(bg)
                else:
                    print("   ⚠️  Фоновые видео повреждены, пропускаем")
            else:
                print("   ⚠️  Фон не найден, пропускаем")

        if self.mode.get("crop"):
            print("   ✂️  Обрезаем под 9:16")
            clip_to_use = clip_to_use.resize(height=self.frame_h)
            if clip_to_use.w > self.frame_w:
                x_center = clip_to_use.w / 2
                clip_to_use = clip_to_use.crop(
                    x1=x_center - self.frame_w / 2,
                    y1=0,
                    x2=x_center + self.frame_w / 2,
                    y2=self.frame_h,
                )

        if self.mode.get("resize_clip"):
            print("   📐 Уменьшаем клип")
            clip_to_use = clip_to_use.resize(width=self.frame_w)
            max_height = self.frame_h * 0.6
            if clip_to_use.h > max_height:
                clip_to_use = clip_to_use.resize(height=max_height)
            y_position = int(self.frame_h * CLIP_VERTICAL_POSITION)
            clip_to_use = clip_to_use.set_position(("center", y_position))

        layers.append(clip_to_use)

        if self.mode.get("banner"):
            banner_files = list(Path(INPUT_BANNERS_DIR).glob("*.mp4"))
            if banner_files:
                banner, banner_path = self._open_first_valid_clip(banner_files, "Баннер")
                if banner is not None:
                    print(f"   🎨 Баннер: {banner_path.name}")
                    banner = chroma_key(banner)
                    if banner.duration < clip.duration:
                        banner = banner.loop(duration=clip.duration)
                    else:
                        banner = banner.subclip(0, clip.duration)
                    layers.append(banner)
                else:
                    print("   ⚠️  Баннеры повреждены, пропускаем")
            else:
                print("   ⚠️  Баннер не найден, пропускаем")

        video = CompositeVideoClip(layers, size=(self.frame_w, self.frame_h))
        if clip.audio:
            video = video.set_audio(clip.audio.volumex(VOICE_VOLUME))
        return video

    def _add_music(self, video):
        """Добавляет фоновую музыку"""
        print(f"   🎵 Музыка: {Path(self.music_path).name}")
        music = AudioFileClip(self.music_path).volumex(DEFAULT_MUSIC_VOLUME)
        if music.duration < video.duration:
            music = music.audio_loop(duration=video.duration)
        else:
            music = music.subclip(0, video.duration)
        mixed_audio = CompositeAudioClip([video.audio, music])
        return video.set_audio(mixed_audio)


class BatchProcessor:
    """Менеджер пакетной обработки"""

    def __init__(self):
        self.clips = self._scan_clips()
        self.music_files = self._scan_music()
        self.output_counter = self._get_next_counter()

    def _scan_clips(self):
        clips = []
        for ext in ["*.mp4", "*.mov", "*.avi", "*.mkv"]:
            clips.extend(Path(INPUT_CLIPS_DIR).glob(ext))
        return sorted(clips)

    def _scan_music(self):
        music = []
        for ext in ["*.mp3", "*.wav", "*.m4a"]:
            music.extend(Path(INPUT_MUSIC_DIR).glob(ext))
        return sorted(music)

    def _get_next_counter(self):
        existing = list(Path(OUTPUT_DIR).glob("**/clip_*.mp4"))
        if not existing:
            return 1
        numbers = []
        for file in existing:
            try:
                numbers.append(int(file.stem.split("_")[1]))
            except Exception:
                continue
        return max(numbers) + 1 if numbers else 1

    def process_queue(self, queue_settings):
        total = len(queue_settings)
        print(f"\n{'='*60}")
        print(f"🚀 НАЧАЛО ПАКЕТНОЙ ОБРАБОТКИ: {total} клипов")
        print(f"{'='*60}\n")

        for idx, settings in enumerate(queue_settings, 1):
            clip_path = str(self.clips[settings["clip_index"]])
            music_path = None
            if settings["music_index"] is not None:
                music_path = str(self.music_files[settings["music_index"]])

            mode = settings["mode"]
            platforms = settings.get("platforms", DEFAULT_PLATFORMS)

            print(f"[{idx}/{total}] Обработка {Path(clip_path).name}")
            processor = VideoProcessor(clip_path, music_path, mode)

            try:
                print("   💬 Генерация субтитров (один раз на клип)...")
                subtitles = generate_subtitles(clip_path)

                for platform in platforms:
                    if platform not in PLATFORM_PROFILES:
                        continue
                    output_filename = f"clip_{self.output_counter}_{platform}.mp4"
                    output_path = os.path.join(OUTPUT_DIR, platform, output_filename)
                    processor.process(output_path, platform, subtitles=subtitles)

                processed_path = os.path.join(PROCESSED_CLIPS_DIR, Path(clip_path).name)
                shutil.move(clip_path, processed_path)
                self.output_counter += 1

            except Exception as e:
                print(f"   ❌ ОШИБКА: {e}\n")
                continue

        print(f"\n{'='*60}")
        print("✅ ОБРАБОТКА ЗАВЕРШЕНА!")
        print(f"   Готовые видео: {OUTPUT_DIR}")
        print(f"   Обработанные клипы: {PROCESSED_CLIPS_DIR}")
        print(f"{'='*60}\n")
