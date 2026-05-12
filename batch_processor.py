"""
Пакетная обработка видео с очередью и поддержкой нескольких платформ
"""
import os
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from moviepy.editor import VideoFileClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip, ImageClip, ColorClip, vfx, afx

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

        if clip.audio:
            audio = clip.audio
            if self.mode.get("type") in {"mirror_bg_and_clip", "mirror_clip_only", "mirror_blur_bars"}:
                audio = self._stylize_audio(audio)
            video = video.set_audio(audio.volumex(VOICE_VOLUME))
        if self.music_path and os.path.exists(self.music_path):
            video = self._add_music(video)

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

    def _apply_speed(self, clip, speed_factor):
        if not speed_factor or abs(speed_factor - 1.0) < 1e-6:
            return clip
        return clip.fx(vfx.speedx, speed_factor)

    def _blur_frame(self, frame):
        img = Image.fromarray(frame)
        return np.array(img.filter(ImageFilter.GaussianBlur(radius=MIRROR_EFFECTS["bg_blur_radius"])))

    def _light_video_tuning(self, frame):
        arr = frame.astype(np.float32)
        arr = arr * MIRROR_EFFECTS["brightness_mul"] + MIRROR_EFFECTS["brightness_add"]
        arr[..., 0] *= MIRROR_EFFECTS["red_mul"]
        arr[..., 1] *= MIRROR_EFFECTS["green_mul"]
        arr[..., 2] *= MIRROR_EFFECTS["blue_mul"]
        noise = np.random.normal(0, MIRROR_EFFECTS["noise_strength"], arr.shape)
        arr += noise
        arr = np.clip(arr, 0, 255)
        return arr.astype(np.uint8)

    def _draw_edge_smiles(self, frame, t, duration):
        img = Image.fromarray(frame)
        draw = ImageDraw.Draw(img, "RGBA")
        w, h = img.size
        size = max(34, int(min(w, h) * MIRROR_EFFECTS["smile_size_ratio"]))
        count = max(1, int(MIRROR_EFFECTS["smile_count"]))
        phase = (t / max(duration, 0.001)) * 6.283
        alpha = int(MIRROR_EFFECTS["smile_alpha"])

        for i in range(count):
            x = int((i + 1) * w / (count + 1) + 24 * np.sin(phase + i))
            y = int(size * 1.3 + 12 * np.cos(phase * 1.4 + i))
            draw.ellipse((x - size, y - size, x + size, y + size), fill=(255, 240, 0, alpha), outline=(20, 20, 20, alpha), width=4)
            eye = max(3, size // 7)
            draw.ellipse((x - size//3 - eye, y - size//4 - eye, x - size//3 + eye, y - size//4 + eye), fill=(0, 0, 0, alpha))
            draw.ellipse((x + size//3 - eye, y - size//4 - eye, x + size//3 + eye, y - size//4 + eye), fill=(0, 0, 0, alpha))
            draw.arc((x - size//2, y - size//5, x + size//2, y + size//2), 15, 165, fill=(0, 0, 0, alpha), width=4)

        return np.array(img)

    def _apply_heavy_visual_effects(self, clip):
        clip = clip.fx(vfx.crop, x_center=clip.w / 2, y_center=clip.h / 2, width=int(clip.w * CENTER_ZOOM_CROP), height=int(clip.h * CENTER_ZOOM_CROP))
        clip = clip.fl_image(self._light_video_tuning)
        clip = clip.fx(vfx.colorx, MIRROR_EFFECTS["color_gain"]).fx(vfx.lum_contrast, lum=MIRROR_EFFECTS["lum"], contrast=MIRROR_EFFECTS["contrast"], contrast_thr=127)
        clip = clip.fl(lambda gf, tt: self._draw_edge_smiles(gf(tt), tt, clip.duration))
        return clip

    def _rounded_rect_mask(self, width, height, radius):
        mask_img = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask_img)
        draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=255)
        mask_np = np.array(mask_img).astype(np.float32) / 255.0
        return mask_np

    def _mode_center_square_custom(self, clip):
        layers = []
        top_margin = 24
        bottom_height = int(self.frame_h * 0.24)
        banner_reserved_height = int(self.frame_h * 0.28)

        static_files = []
        search_dirs = [Path(ROOT_PNG_DIR), Path(INPUT_STATIC_BACKGROUNDS_DIR)]
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            files = [
                p for p in search_dir.iterdir()
                if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
            ]
            if files:
                static_files = files
                print(f"   🖼️  Статичный фон: {files[0].name} (из {search_dir})")
                break
        if static_files:
            static_bg = ImageClip(str(static_files[0])).set_duration(clip.duration)
            static_bg = static_bg.resize(height=self.frame_h)
            if static_bg.w < self.frame_w:
                static_bg = static_bg.resize(width=self.frame_w)
            static_bg = static_bg.crop(
                x_center=static_bg.w / 2,
                y_center=static_bg.h / 2,
                width=self.frame_w,
                height=self.frame_h,
            )
            layers.append(static_bg)
        else:
            print(f"   ⚠️  Статичный PNG/JPG фон не найден в: {ROOT_PNG_DIR} и {INPUT_STATIC_BACKGROUNDS_DIR}")

        bg_files = list(Path(INPUT_BACKGROUNDS_DIR).glob("*.mp4"))
        if bg_files:
            bottom_bg = VideoFileClip(str(bg_files[0])).without_audio()
            if bottom_bg.duration < clip.duration:
                bottom_bg = bottom_bg.loop(duration=clip.duration)
            else:
                bottom_bg = bottom_bg.subclip(0, clip.duration)
            bottom_bg = bottom_bg.resize(width=self.frame_w)
            if bottom_bg.h < bottom_height:
                bottom_bg = bottom_bg.resize(height=bottom_height)
            bottom_bg = bottom_bg.crop(x_center=bottom_bg.w / 2, y_center=bottom_bg.h / 2, width=self.frame_w, height=bottom_height)
            bottom_bg = bottom_bg.set_position(("center", self.frame_h - bottom_height))
            layers.append(bottom_bg)

        available_top = top_margin + banner_reserved_height + 24
        available_bottom = self.frame_h - bottom_height - 24
        center_height = max(420, int((available_bottom - available_top) * 0.96))
        square_size = min(int(self.frame_w * 0.78), int(center_height * 1.15))
        center_clip = clip.fx(vfx.mirror_x).without_audio()
        pre_crop_width = int(center_clip.w * 0.78)
        center_clip = center_clip.crop(
            x_center=center_clip.w / 2,
            y_center=center_clip.h / 2,
            width=pre_crop_width,
            height=center_clip.h,
        )
        center_clip = center_clip.resize(height=square_size)
        if center_clip.w < square_size:
            center_clip = center_clip.resize(width=square_size)
        center_clip = center_clip.crop(
            x_center=center_clip.w / 2,
            y_center=center_clip.h / 2,
            width=square_size,
            height=center_height,
        )

        radius = int(center_height * 0.1)
        mask = ImageClip(self._rounded_rect_mask(square_size, center_height, radius), ismask=True).set_duration(clip.duration)
        center_clip = center_clip.set_mask(mask)

        border = ColorClip(size=(square_size + 26, center_height + 26), color=(255, 255, 255), duration=clip.duration)
        border_mask = ImageClip(
            self._rounded_rect_mask(square_size + 26, center_height + 26, radius + 12),
            ismask=True,
        ).set_duration(clip.duration)
        video_y = min(available_top, self.frame_h - bottom_height - center_height - 30)
        border = border.set_mask(border_mask).set_position(("center", video_y - 13))

        center_clip = center_clip.set_position(("center", video_y))
        layers.append(border)
        layers.append(center_clip)

        if self.mode.get("banner"):
            banner_files = list(Path(INPUT_BANNERS_DIR).glob("*.mp4"))
            if banner_files:
                banner = VideoFileClip(str(banner_files[0])).without_audio()
                banner = banner.loop(duration=clip.duration) if banner.duration < clip.duration else banner.subclip(0, clip.duration)
                banner = chroma_key(banner).set_duration(clip.duration)
                banner = banner.set_position(("center", top_margin))
                layers.append(banner)

        composed = CompositeVideoClip(layers, size=(self.frame_w, self.frame_h))
        return composed.fl(lambda gf, tt: self._draw_edge_smiles(gf(tt), tt, clip.duration))

    def _mode_universal(self, clip):
        print(f"   🎬 Режим: {self.mode['name']}")
        if self.mode.get("type") == "center_square_custom":
            return self._mode_center_square_custom(clip)

        layers = []
        clip_to_use = clip

        if self.mode.get("type") in {"mirror_bg_and_clip", "mirror_blur_bars"}:
            bg_speed = self.mode.get("background_speed", MIRROR_EFFECTS["audio_speed"])
            bg = self._apply_speed(clip.without_audio(), bg_speed).fx(vfx.mirror_x)
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
        if self.mode.get("type") in {"mirror_bg_and_clip", "mirror_clip_only", "mirror_blur_bars"}:
            clip_speed = 1.10

        clip_to_use = self._apply_speed(clip_to_use, clip_speed)

        if self.mode.get("mirror_clip"):
            clip_to_use = clip_to_use.fx(vfx.mirror_x)

        if self.mode.get("type") in {"mirror_bg_and_clip", "mirror_clip_only", "mirror_blur_bars"}:
            clip_to_use = self._apply_heavy_visual_effects(clip_to_use)

        if self.mode.get("crop"):
            clip_to_use = clip_to_use.resize(height=self.frame_h)
            if clip_to_use.w > self.frame_w:
                x_center = clip_to_use.w / 2
                clip_to_use = clip_to_use.crop(x1=x_center - self.frame_w / 2, y1=0, x2=x_center + self.frame_w / 2, y2=self.frame_h)

        if self.mode.get("type") == "mirror_blur_bars":
            clip_to_use = clip_to_use.resize(width=self.frame_w)
            if clip_to_use.h > self.frame_h:
                clip_to_use = clip_to_use.resize(height=self.frame_h)
            clip_to_use = clip_to_use.set_position(("center", "center"))
        elif self.mode.get("resize_clip"):
            clip_to_use = clip_to_use.resize(width=self.frame_w)
            max_height = self.frame_h * MIRROR_EFFECTS["zoom_ratio"]
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

    def _stylize_audio(self, audio_clip):
        """Изменяет звук, чтобы он отличался от оригинала в зеркальных режимах."""
        styled = audio_clip.fx(afx.audio_normalize)
        styled = styled.fx(afx.audio_fadein, 0.05).fx(afx.audio_fadeout, 0.05)
        styled = styled.set_fps(44100)
        styled = styled.fx(vfx.speedx, MIRROR_EFFECTS["audio_speed"])
        styled = styled.set_fps(MIRROR_EFFECTS["audio_pitch_rate"]).set_fps(44100)
        return styled.volumex(MIRROR_EFFECTS["audio_volume_boost"])

    def _add_music(self, video):
        """Добавляет фоновую музыку к видео."""
        music = AudioFileClip(self.music_path).volumex(DEFAULT_MUSIC_VOLUME)
        if music.duration < video.duration:
            music = music.audio_loop(duration=video.duration)
        else:
            music = music.subclip(0, video.duration)

        if video.audio is None:
            return video.set_audio(music)

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
