"""
Главный скрипт запуска - пакетная обработка YouTube Shorts
"""
import sys
from terminal_ui import main as run_ui


def print_welcome():
    """Приветственное сообщение"""
    print("\n" + "="*60)
    print("🎬 YOUTUBE SHORTS - АВТОМАТИЧЕСКАЯ ОБРАБОТКА ВИДЕО")
    print("="*60)
    print("\n📋 ИНСТРУКЦИЯ:")
    print("  1. Положите видео в: input/clips/")
    print("  2. Положите музыку в: input/music/")
    print("  3. Положите фоны в: input/backgrounds/")
    print("  4. Положите баннеры в: input/banners/")
    print("\n🚀 Программа запускается...\n")


if __name__ == "__main__":
    print_welcome()

    try:
        run_ui()
    except KeyboardInterrupt:
        print("\n\n⚠️  Программа остановлена пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        input("Нажмите Enter для выхода...")
        sys.exit(1)