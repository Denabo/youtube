"""
Пакетная обработка видео с очередью и поддержкой нескольких платформ
"""
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from moviepy.editor import VideoFileClip, CompositeVideoClip, vfx

from config import *
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

    def process(self, output_path, platform_key):
        """Главная функция обработки видео"""
        profile = PLATFORM_PROFILES[platform_key]
        self.frame_w = profile["width"]
        self.frame_h = profile["height"]

        print(f"⚙️  Обработка: {self.clip_name} -> {profile['name']}")
        clip = VideoFileClip(self.clip_path)

        video = self._mode_universal(clip)

        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        print("   💬 Генерация субтитров...")
        subtitles = generate_subtitles(self.clip_path)
        video = add_stylish_subtitles(video, subtitles)

        temp_output = output_path
        final_output = output_path
        needs_audio_post = self.mode.get("type") in {"mirror_bg_and_clip", "mirror_clip_only"}
        if needs_audio_post:
            temp_output = str(Path(output_path).with_suffix(".tmp_video.mp4"))

        print("   💾 Рендер видео...")
        video.write_videofile(
            temp_output,
            codec="libx264",
            audio=False,
            fps=profile["fps"],
            threads=RENDER_THREADS,
            preset=RENDER_PRESET,
            bitrate=RENDER_BITRATE,
            logger=None,
        )

        if needs_audio_post:
            self._attach_filtered_audio(temp_output, final_output)
            Path(temp_output).unlink(missing_ok=True)

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

    def _apply_speed(self, clip, speed_factor):
        if not speed_factor or abs(speed_factor - 1.0) < 1e-6:
            return clip
        return clip.fx(vfx.speedx, speed_factor)

    def _blur_frame(self, frame):
        img = Image.fromarray(frame)
        return np.array(img.filter(ImageFilter.GaussianBlur(radius=10)))

    def _light_video_tuning(self, frame):
        arr = frame.astype(np.float32)
        arr = arr * 1.03 + 4.0
        arr[..., 1] *= 1.02
        arr[..., 2] *= 0.99
        arr = np.clip(arr, 0, 255)
        return arr.astype(np.uint8)

    def _mode_universal(self, clip):
        print(f"   🎬 Режим: {self.mode['name']}")
        layers = []
        clip_to_use = clip

        if self.mode.get("type") == "mirror_bg_and_clip":
            bg = self._apply_speed(clip.without_audio(), 0.90).fx(vfx.mirror_x)
            bg = self._fit_background(bg, clip.duration)
            bg = bg.fl_image(self._blur_frame).set_duration(clip.duration)
            layers.append(bg)
        elif self.mode.get("background"):
            bg_files = list(Path(INPUT_BACKGROUNDS_DIR).glob("*.mp4"))
            if bg_files:
                print(f"   🖼️  Фон: {bg_files[0].name}")
                bg = VideoFileClip(str(bg_files[0])).without_audio()
                bg = self._fit_background(bg, clip.duration)
                layers.append(bg)
            else:
                print("   ⚠️  Фон не найден, пропускаем")

        clip_speed = self.mode.get("clip_speed", 1.0)
        if self.mode.get("type") in {"mirror_bg_and_clip", "mirror_clip_only"}:
            clip_speed = 1.10

        clip_to_use = self._apply_speed(clip_to_use, clip_speed)

        if self.mode.get("mirror_clip"):
            clip_to_use = clip_to_use.fx(vfx.mirror_x)

        if self.mode.get("type") in {"mirror_bg_and_clip", "mirror_clip_only"}:
            clip_to_use = clip_to_use.fx(vfx.crop, x_center=clip_to_use.w / 2, y_center=clip_to_use.h / 2, width=int(clip_to_use.w * 0.98), height=int(clip_to_use.h * 0.98))
            clip_to_use = clip_to_use.fl_image(self._light_video_tuning)

        if self.mode.get("crop"):
            clip_to_use = clip_to_use.resize(height=self.frame_h)
            if clip_to_use.w > self.frame_w:
                x_center = clip_to_use.w / 2
                clip_to_use = clip_to_use.crop(x1=x_center - self.frame_w / 2, y1=0, x2=x_center + self.frame_w / 2, y2=self.frame_h)

        if self.mode.get("resize_clip"):
            clip_to_use = clip_to_use.resize(width=self.frame_w)
            max_height = self.frame_h * 0.6
            if clip_to_use.h > max_height:
                clip_to_use = clip_to_use.resize(height=max_height)
            y_position = int(self.frame_h * CLIP_VERTICAL_POSITION)
            clip_to_use = clip_to_use.set_position(("center", y_position))
        else:
            clip_to_use = clip_to_use.set_position(("center", "center"))

        layers.append(clip_to_use)

        if self.mode.get("banner"):
            banner_files = list(Path(INPUT_BANNERS_DIR).glob("*.mp4"))
            if banner_files:
                banner = VideoFileClip(str(banner_files[0])).without_audio()
                if banner.duration < clip.duration:
                    banner = banner.loop(duration=clip.duration)
                else:
                    banner = banner.subclip(0, clip.duration)
                banner = chroma_key(banner).set_start(0).set_duration(clip.duration)
                banner = banner.set_position(("center", BANNER_VERTICAL_POSITION))
                layers.append(banner)

        return CompositeVideoClip(layers, size=(self.frame_w, self.frame_h))

    def _attach_filtered_audio(self, rendered_video_path, output_path):
        audio_chain = "atempo=1.10,asetrate=44100*1.03,aresample=44100,highpass=f=120,lowpass=f=9000"
        cmd = ["ffmpeg", "-y", "-i", rendered_video_path, "-i", self.clip_path]

        if self.music_path and os.path.exists(self.music_path):
            cmd += ["-i", self.music_path]
            filter_complex = (
                f"[1:a]{audio_chain},volume=1.0[voc];"
                "[2:a]volume=0.05623413251903491,aresample=44100[mus];"
                "[voc][mus]amix=inputs=2:duration=first[aout]"
            )
        else:
            filter_complex = f"[1:a]{audio_chain}[aout]"

        cmd += [
            "-filter_complex",
            filter_complex,
            "-map",
            "0:v:0",
            "-map",
            "[aout]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            output_path,
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


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
                for platform in platforms:
                    if platform not in PLATFORM_PROFILES:
                        continue
                    output_filename = f"clip_{self.output_counter}_{platform}.mp4"
                    output_path = os.path.join(OUTPUT_DIR, platform, output_filename)
                    processor.process(output_path, platform)

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
