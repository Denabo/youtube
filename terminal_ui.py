"""
Терминальный интерфейс для управления обработкой
"""
import os
from pathlib import Path
from batch_processor import BatchProcessor
from config import PROCESSING_MODES, INPUT_CLIPS_DIR, INPUT_MUSIC_DIR


class TerminalUI:
    """Интерфейс командной строки"""

    def __init__(self):
        self.processor = BatchProcessor()
        self.queue = []

    def clear_screen(self):
        """Очищает экран"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        """Печатает заголовок"""
        print("\n" + "="*60)
        print("🎬 YOUTUBE SHORTS - ПАКЕТНАЯ ОБРАБОТКА ВИДЕО")
        print("="*60 + "\n")

    def show_main_menu(self):
        """Главное меню"""
        while True:
            self.clear_screen()
            self.print_header()

            # Статистика
            print(f"📁 Клипов в очереди: {len(self.processor.clips)}")
            print(f"🎵 Музыкальных треков: {len(self.processor.music_files)}")
            print(f"📋 Задач в обработке: {len(self.queue)}\n")

            print("МЕНЮ:")
            print("  1. Просмотреть клипы")
            print("  2. Просмотреть музыку")
            print("  3. Создать очередь обработки")
            print("  4. Запустить обработку")
            print("  5. Выход")

            choice = input("\nВыберите действие (1-5): ").strip()

            if choice == "1":
                self.show_clips()
            elif choice == "2":
                self.show_music()
            elif choice == "3":
                self.create_queue()
            elif choice == "4":
                self.start_processing()
            elif choice == "5":
                print("\n👋 До свидания!\n")
                break
            else:
                print("❌ Неверный выбор!")
                input("Нажмите Enter...")

    def show_clips(self):
        """Показывает список клипов"""
        self.clear_screen()
        self.print_header()

        if not self.processor.clips:
            print(f"❌ Клипы не найдены в папке: {INPUT_CLIPS_DIR}\n")
            input("Нажмите Enter...")
            return

        print("📹 ДОСТУПНЫЕ КЛИПЫ:\n")
        for idx, clip in enumerate(self.processor.clips):
            size_mb = clip.stat().st_size / (1024 * 1024)
            print(f"  [{idx}] {clip.name} ({size_mb:.1f} МБ)")

        print()
        input("Нажмите Enter для возврата...")

    def show_music(self):
        """Показывает список музыки"""
        self.clear_screen()
        self.print_header()

        if not self.processor.music_files:
            print(f"❌ Музыка не найдена в папке: {INPUT_MUSIC_DIR}\n")
            input("Нажмите Enter...")
            return

        print("🎵 ДОСТУПНАЯ МУЗЫКА:\n")
        for idx, music in enumerate(self.processor.music_files):
            size_mb = music.stat().st_size / (1024 * 1024)
            print(f"  [{idx}] {music.name} ({size_mb:.1f} МБ)")

        print()
        input("Нажмите Enter для возврата...")

    def create_queue(self):
        """Создаёт очередь обработки"""
        self.clear_screen()
        self.print_header()

        if not self.processor.clips:
            print(f"❌ Нет клипов для обработки!\n")
            input("Нажмите Enter...")
            return

        print("🔧 СОЗДАНИЕ ОЧЕРЕДИ ОБРАБОТКИ\n")

        # Режим создания очереди
        print("Выберите режим:")
        print("  1. Настроить каждый клип отдельно")
        print("  2. Применить одинаковые настройки ко всем")

        mode_choice = input("\nВыбор (1-2): ").strip()

        if mode_choice == "1":
            self._create_queue_individual()
        elif mode_choice == "2":
            self._create_queue_batch()
        else:
            print("❌ Неверный выбор!")
            input("Нажмите Enter...")

    def _create_queue_individual(self):
        """Настройка каждого клипа отдельно"""
        self.queue = []

        for idx, clip in enumerate(self.processor.clips):
            self.clear_screen()
            self.print_header()

            print(f"Настройка клипа [{idx+1}/{len(self.processor.clips)}]")
            print(f"📹 {clip.name}\n")

            # Выбор режима обработки
            print("Режим обработки:")
            for key, mode_info in PROCESSING_MODES.items():
                print(f"  {key}. {mode_info['name']}")

            mode = input("\nВыбор (1-2): ").strip()
            if mode not in PROCESSING_MODES:
                mode = "1"

            # Выбор музыки
            print("\nМузыка:")
            print("  0. Без музыки")

            for m_idx, music in enumerate(self.processor.music_files, 1):
                print(f"  {m_idx}. {music.name}")

            music_choice = input(f"\nВыбор (0-{len(self.processor.music_files)}): ").strip()

            try:
                music_idx = int(music_choice)
                if music_idx == 0:
                    music_index = None
                elif 1 <= music_idx <= len(self.processor.music_files):
                    music_index = music_idx - 1
                else:
                    music_index = None
            except:
                music_index = None

            self.queue.append({
                'clip_index': idx,
                'music_index': music_index,
                'mode': mode
            })

            print(f"\n✅ Клип добавлен в очередь")

        print(f"\n✅ Очередь создана: {len(self.queue)} клипов")
        input("Нажмите Enter...")

    def _create_queue_batch(self):
        """Одинаковые настройки для всех"""
        self.clear_screen()
        self.print_header()

        print("🔧 НАСТРОЙКИ ДЛЯ ВСЕХ КЛИПОВ\n")

        # Выбор режима
        print("Режим обработки:")
        for key, mode_info in PROCESSING_MODES.items():
            print(f"  {key}. {mode_info['name']}")

        mode = input("\nВыбор (1-2): ").strip()
        if mode not in PROCESSING_MODES:
            mode = "1"

        # Выбор музыки
        print("\nМузыка:")
        print("  0. Без музыки")
        print("  -1. Случайная для каждого клипа")

        for m_idx, music in enumerate(self.processor.music_files, 1):
            print(f"  {m_idx}. {music.name}")

        music_choice = input(f"\nВыбор (-1 до {len(self.processor.music_files)}): ").strip()

        self.queue = []

        for idx in range(len(self.processor.clips)):
            if music_choice == "-1":
                # Случайная музыка
                music_index = idx % len(self.processor.music_files) if self.processor.music_files else None
            elif music_choice == "0":
                music_index = None
            else:
                try:
                    music_idx = int(music_choice)
                    if 1 <= music_idx <= len(self.processor.music_files):
                        music_index = music_idx - 1
                    else:
                        music_index = None
                except:
                    music_index = None

            self.queue.append({
                'clip_index': idx,
                'music_index': music_index,
                'mode': mode
            })

        print(f"\n✅ Очередь создана: {len(self.queue)} клипов")
        input("Нажмите Enter...")

    def start_processing(self):
        """Запускает обработку"""
        self.clear_screen()
        self.print_header()

        if not self.queue:
            print("❌ Очередь пуста! Сначала создайте очередь.\n")
            input("Нажмите Enter...")
            return

        print(f"🚀 ГОТОВО К ЗАПУСКУ\n")
        print(f"   Клипов в очереди: {len(self.queue)}")
        print(f"   Начальный номер: clip_{self.processor.output_counter}.mp4\n")

        confirm = input("Начать обработку? (y/n): ").strip().lower()

        if confirm != 'y':
            print("\n❌ Отменено")
            input("Нажмите Enter...")
            return

        # Запускаем обработку
        print()
        self.processor.process_queue(self.queue)

        # Очищаем очередь
        self.queue = []

        # Обновляем список клипов
        self.processor.clips = self.processor._scan_clips()

        input("\nНажмите Enter для возврата в меню...")


def main():
    """Запуск интерфейса"""
    ui = TerminalUI()
    ui.show_main_menu()


if __name__ == "__main__":
    main()