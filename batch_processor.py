"""
Пакетная обработка видео с очередью
"""
import os
import shutil
from pathlib import Path
from moviepy.editor import VideoFileClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip
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

    def process(self, output_path):
        """Главная функция обработки видео"""
        print(f"⚙️  Обработка: {self.clip_name}")

        # Загружаем клип
        clip = VideoFileClip(self.clip_path)

        # Выбираем режим обработки
        if self.mode["crop"]:
            video = self._mode_crop_with_banner(clip)
        else:
            video = self._mode_minecraft_background(clip)

        # Добавляем музыку
        if self.music_path and os.path.exists(self.music_path):
            video = self._add_music(video)

        # Генерируем субтитры
        print(f"   💬 Генерация субтитров...")
        subtitles = generate_subtitles(self.clip_path)
        video = add_stylish_subtitles(video, subtitles)

        # Рендерим
        print(f"   💾 Рендер видео...")
        video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=FPS,
            threads=RENDER_THREADS,
            preset=RENDER_PRESET,
            bitrate=RENDER_BITRATE,
            logger=None  # Убираем логи MoviePy
        )

        clip.close()
        video.close()
        print(f"   ✅ Готово: {Path(output_path).name}\n")

    def _mode_crop_with_banner(self, clip):
        """Режим 1: Обрезка клипа + баннер без фона"""
        print(f"   🎬 Режим: Обрезка + Баннер")

        # Обрезаем клип под формат 9:16
        clip_resized = clip.resize(height=SHORTS_HEIGHT)
        if clip_resized.w > SHORTS_WIDTH:
            x_center = clip_resized.w / 2
            clip_resized = clip_resized.crop(
                x1=x_center - SHORTS_WIDTH/2,
                y1=0,
                x2=x_center + SHORTS_WIDTH/2,
                y2=SHORTS_HEIGHT
            )

        # Загружаем баннер
        banner_files = list(Path(INPUT_BANNERS_DIR).glob("*.mp4"))
        if banner_files:
            banner_path = str(banner_files[0])
            print(f"   🎨 Баннер: {Path(banner_path).name}")

            banner = VideoFileClip(banner_path).without_audio()
            banner = chroma_key(banner)

            # Зацикливаем баннер
            if banner.duration < clip_resized.duration:
                repeats = int(clip_resized.duration / banner.duration) + 1
                banner = banner.loop(duration=clip_resized.duration)
            else:
                banner = banner.subclip(0, clip_resized.duration)

            layers = [clip_resized, banner]
        else:
            layers = [clip_resized]

        video = CompositeVideoClip(layers, size=(SHORTS_WIDTH, SHORTS_HEIGHT))
        video = video.set_audio(clip_resized.audio.volumex(VOICE_VOLUME))
        return video

    def _mode_minecraft_background(self, clip):
        """Режим 2: Майнкрафт фон + уменьшенный клип"""
        print(f"   🎬 Режим: Майнкрафт фон")

        # Загружаем фон
        bg_files = list(Path(INPUT_BACKGROUNDS_DIR).glob("*.mp4"))
        if not bg_files:
            raise FileNotFoundError("Фоновое видео не найдено!")

        bg_path = str(bg_files[0])
        print(f"   🖼️  Фон: {Path(bg_path).name}")

        bg = VideoFileClip(bg_path).without_audio()
        bg = bg.resize(height=SHORTS_HEIGHT)
        if bg.w > SHORTS_WIDTH:
            x_center = bg.w / 2
            bg = bg.crop(
                x1=x_center - SHORTS_WIDTH / 2,
                y1=0,
                x2=x_center + SHORTS_WIDTH / 2,
                y2=SHORTS_HEIGHT
            )

        # Зацикливаем фон
        if bg.duration < clip.duration:
            bg = bg.loop(duration=clip.duration)
        else:
            bg = bg.subclip(0, clip.duration)

        # Уменьшаем клип
        clip_resized = clip.resize(width=SHORTS_WIDTH)
        max_height = SHORTS_HEIGHT * 0.6
        if clip_resized.h > max_height:
            clip_resized = clip_resized.resize(height=max_height)

        y_position = int(SHORTS_HEIGHT * CLIP_VERTICAL_POSITION)
        clip_resized = clip_resized.set_position(("center", y_position))

        # ДУБЛИРУЕМ КОД ДЛЯ БАННЕРА ИЗ ПЕРВОГО РЕЖИМА
        # Загружаем баннер
        banner_files = list(Path(INPUT_BANNERS_DIR).glob("*.mp4"))
        if banner_files:
            banner_path = str(banner_files[0])
            print(f"   🎨 Баннер: {Path(banner_path).name}")

            banner = VideoFileClip(banner_path).without_audio()
            banner = chroma_key(banner)

            # Зацикливаем баннер под длину клипа (не clip_resized!)
            # Важно: используем clip.duration, так как это оригинальная длина
            if banner.duration < clip.duration:
                repeats = int(clip.duration / banner.duration) + 1
                banner = banner.loop(duration=clip.duration)
            else:
                banner = banner.subclip(0, clip.duration)

            layers = [bg, clip_resized, banner]  # Баннер поверх всего
        else:
            layers = [bg, clip_resized]  # Только фон и клип

        video = CompositeVideoClip(layers, size=(SHORTS_WIDTH, SHORTS_HEIGHT))
        video = video.set_audio(clip_resized.audio.volumex(VOICE_VOLUME))
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

    def _mode_circle_crop(self, clip):
        """Режим 3: Круговая обрезка (TikTok стиль)"""
        print(f"   🎬 Режим: Круговая обрезка")

        # Обрезаем под 9:16
        clip_resized = clip.resize(height=SHORTS_HEIGHT)
        if clip_resized.w > SHORTS_WIDTH:
            x_center = clip_resized.w / 2
            clip_resized = clip_resized.crop(
                x1=x_center - SHORTS_WIDTH/2,
                y1=0,
                x2=x_center + SHORTS_WIDTH/2,
                y2=SHORTS_HEIGHT
            )

        # TODO: Добавить круговую маску (требует PIL)
        # Пока просто обрезка

        video = CompositeVideoClip([clip_resized], size=(SHORTS_WIDTH, SHORTS_HEIGHT))
        video = video.set_audio(clip_resized.audio.volumex(VOICE_VOLUME))
        return video

    def _mode_split_screen(self, clip):
        """Режим 4: Двойной экран (реакция на видео)"""
        print(f"   🎬 Режим: Двойной экран")

        # Загружаем фон
        bg_files = list(Path(INPUT_BACKGROUNDS_DIR).glob("*.mp4"))
        if not bg_files:
            raise FileNotFoundError("Фоновое видео не найдено!")

        bg = VideoFileClip(str(bg_files[0])).without_audio()
        bg = bg.resize(height=SHORTS_HEIGHT)
        if bg.w > SHORTS_WIDTH:
            x_center = bg.w / 2
            bg = bg.crop(
                x1=x_center - SHORTS_WIDTH/2,
                y1=0,
                x2=x_center + SHORTS_WIDTH/2,
                y2=SHORTS_HEIGHT
            )

        # Зацикливаем
        if bg.duration < clip.duration:
            bg = bg.loop(duration=clip.duration)
        else:
            bg = bg.subclip(0, clip.duration)

        # Уменьшаем клип (занимает 40% высоты)
        clip_resized = clip.resize(width=SHORTS_WIDTH)
        max_height = SHORTS_HEIGHT * 0.4
        if clip_resized.h > max_height:
            clip_resized = clip_resized.resize(height=max_height)

        # Размещаем сверху (split_position = "top")
        split_pos = self.mode.get("split_position", "top")
        if split_pos == "top":
            y_position = 50
        else:  # bottom
            y_position = SHORTS_HEIGHT - clip_resized.h - 50

        clip_resized = clip_resized.set_position(("center", y_position))

        video = CompositeVideoClip([bg, clip_resized], size=(SHORTS_WIDTH, SHORTS_HEIGHT))
        video = video.set_audio(clip_resized.audio.volumex(VOICE_VOLUME))
        return video

    def _mode_full_package(self, clip):
        """Режим 5: Всё вместе (Фон + Баннер + Клип)"""
        print(f"   🎬 Режим: Полный пакет")

        # 1. Загружаем фон
        bg_files = list(Path(INPUT_BACKGROUNDS_DIR).glob("*.mp4"))
        if not bg_files:
            raise FileNotFoundError("Фоновое видео не найдено!")

        bg = VideoFileClip(str(bg_files[0])).without_audio()
        bg = bg.resize(height=SHORTS_HEIGHT)
        if bg.w > SHORTS_WIDTH:
            x_center = bg.w / 2
            bg = bg.crop(
                x1=x_center - SHORTS_WIDTH/2,
                y1=0,
                x2=x_center + SHORTS_WIDTH/2,
                y2=SHORTS_HEIGHT
            )

        if bg.duration < clip.duration:
            bg = bg.loop(duration=clip.duration)
        else:
            bg = bg.subclip(0, clip.duration)

        # 2. Уменьшаем клип
        clip_resized = clip.resize(width=SHORTS_WIDTH)
        max_height = SHORTS_HEIGHT * 0.6
        if clip_resized.h > max_height:
            clip_resized = clip_resized.resize(height=max_height)

        y_position = int(SHORTS_HEIGHT * CLIP_VERTICAL_POSITION)
        clip_resized = clip_resized.set_position(("center", y_position))

        # 3. Загружаем баннер
        layers = [bg, clip_resized]

        banner_files = list(Path(INPUT_BANNERS_DIR).glob("*.mp4"))
        if banner_files:
            banner = VideoFileClip(str(banner_files[0])).without_audio()
            banner = chroma_key(banner)

            if banner.duration < clip.duration:
                banner = banner.loop(duration=clip.duration)
            else:
                banner = banner.subclip(0, clip.duration)

            layers.append(banner)

        video = CompositeVideoClip(layers, size=(SHORTS_WIDTH, SHORTS_HEIGHT))
        video = video.set_audio(clip_resized.audio.volumex(VOICE_VOLUME))
        return video

    def _mode_universal(self, clip):
        """УНИВЕРСАЛЬНЫЙ РЕЖИМ - автоматически проверяет все параметры"""
        print(f"   🎬 Режим: Универсальный")

        layers = []
        clip_to_use = clip

        # === ШАГ 1: ФОН (если нужен) ===
        if self.mode.get("background"):
            print(f"   🖼️  Загружаем фон...")
            bg_files = list(Path(INPUT_BACKGROUNDS_DIR).glob("*.mp4"))

            if bg_files:
                bg = VideoFileClip(str(bg_files[0])).without_audio()

                # Подгоняем под формат
                bg = bg.resize(height=SHORTS_HEIGHT)
                if bg.w > SHORTS_WIDTH:
                    x_center = bg.w / 2
                    bg = bg.crop(
                        x1=x_center - SHORTS_WIDTH/2,
                        y1=0,
                        x2=x_center + SHORTS_WIDTH/2,
                        y2=SHORTS_HEIGHT
                    )

                # Зацикливаем
                if bg.duration < clip.duration:
                    bg = bg.loop(duration=clip.duration)
                else:
                    bg = bg.subclip(0, clip.duration)

                layers.append(bg)
            else:
                print(f"   ⚠️  Фон не найден, пропускаем")

        # === ШАГ 2: ОБРЕЗКА КЛИПА (если нужна) ===
        if self.mode.get("crop"):
            print(f"   ✂️  Обрезаем клип под 9:16...")
            clip_to_use = clip.resize(height=SHORTS_HEIGHT)

            if clip_to_use.w > SHORTS_WIDTH:
                x_center = clip_to_use.w / 2
                clip_to_use = clip_to_use.crop(
                    x1=x_center - SHORTS_WIDTH/2,
                    y1=0,
                    x2=x_center + SHORTS_WIDTH/2,
                    y2=SHORTS_HEIGHT
                )

        # === ШАГ 3: УМЕНЬШЕНИЕ КЛИПА (если нужно) ===
        if self.mode.get("resize_clip"):
            print(f"   📐 Уменьшаем клип...")
            clip_to_use = clip_to_use.resize(width=SHORTS_WIDTH)

            # Максимальная высота (60% экрана)
            max_height = SHORTS_HEIGHT * 0.6
            if clip_to_use.h > max_height:
                clip_to_use = clip_to_use.resize(height=max_height)

            # Позиционируем
            y_position = int(SHORTS_HEIGHT * CLIP_VERTICAL_POSITION)
            clip_to_use = clip_to_use.set_position(("center", y_position))

        # Добавляем клип
        layers.append(clip_to_use)

        # === ШАГ 4: БАННЕР (если нужен) ===
        if self.mode.get("banner"):
            print(f"   🎨 Загружаем баннер...")
            banner_files = list(Path(INPUT_BANNERS_DIR).glob("*.mp4"))

            if banner_files:
                banner = VideoFileClip(str(banner_files[0])).without_audio()

                # Хромакей
                banner = chroma_key(banner)

                # Зацикливаем
                if banner.duration < clip.duration:
                    banner = banner.loop(duration=clip.duration)
                else:
                    banner = banner.subclip(0, clip.duration)

                layers.append(banner)
            else:
                print(f"   ⚠️  Баннер не найден, пропускаем")

        # === СБОРКА ===
        if len(layers) == 0:
            # Если ничего не добавили, используем просто клип
            layers = [clip]

        video = CompositeVideoClip(layers, size=(SHORTS_WIDTH, SHORTS_HEIGHT))

        # Аудио берём от оригинального клипа
        if clip.audio:
            video = video.set_audio(clip.audio.volumex(VOICE_VOLUME))

        return video


class BatchProcessor:
    """Менеджер пакетной обработки"""

    def __init__(self):
        self.clips = self._scan_clips()
        self.music_files = self._scan_music()
        self.output_counter = self._get_next_counter()

    def _scan_clips(self):
        """Сканирует папку с клипами"""
        clips = []
        for ext in ['*.mp4', '*.mov', '*.avi', '*.mkv']:
            clips.extend(Path(INPUT_CLIPS_DIR).glob(ext))
        return sorted(clips)

    def _scan_music(self):
        """Сканирует папку с музыкой"""
        music = []
        for ext in ['*.mp3', '*.wav', '*.m4a']:
            music.extend(Path(INPUT_MUSIC_DIR).glob(ext))
        return sorted(music)

    def _get_next_counter(self):
        """Определяет номер следующего видео"""
        existing = list(Path(OUTPUT_DIR).glob("clip_*.mp4"))
        if not existing:
            return 1

        numbers = []
        for f in existing:
            try:
                num = int(f.stem.split('_')[1])
                numbers.append(num)
            except:
                continue

        return max(numbers) + 1 if numbers else 1

    def process_queue(self, queue_settings):
        """Обрабатывает очередь видео

        queue_settings: список словарей с настройками для каждого клипа
        Формат: [
            {'clip_index': 0, 'music_index': 0, 'mode': '1'},
            {'clip_index': 1, 'music_index': None, 'mode': '2'},
        ]
        """
        total = len(queue_settings)

        print(f"\n{'='*60}")
        print(f"🚀 НАЧАЛО ПАКЕТНОЙ ОБРАБОТКИ: {total} видео")
        print(f"{'='*60}\n")

        for idx, settings in enumerate(queue_settings, 1):
            clip_path = str(self.clips[settings['clip_index']])

            music_path = None
            if settings['music_index'] is not None:
                music_path = str(self.music_files[settings['music_index']])

            mode = settings['mode']

            # Создаём процессор
            processor = VideoProcessor(clip_path, music_path, mode)

            # Формируем путь вывода
            output_filename = f"clip_{self.output_counter}.mp4"
            output_path = os.path.join(OUTPUT_DIR, output_filename)

            print(f"[{idx}/{total}] Обработка видео...")

            try:
                processor.process(output_path)

                # Перемещаем обработанный клип
                processed_path = os.path.join(PROCESSED_CLIPS_DIR, Path(clip_path).name)
                shutil.move(clip_path, processed_path)

                self.output_counter += 1

            except Exception as e:
                print(f"   ❌ ОШИБКА: {e}\n")
                continue

        print(f"\n{'='*60}")
        print(f"✅ ОБРАБОТКА ЗАВЕРШЕНА!")
        print(f"   Готовые видео: {OUTPUT_DIR}")
        print(f"   Обработанные клипы: {PROCESSED_CLIPS_DIR}")
        print(f"{'='*60}\n")