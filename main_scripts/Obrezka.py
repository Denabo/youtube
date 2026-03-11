"""Совместимость со старым названием скрипта нарезки.
Запускает новый cutter: ../video_cutter.py
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from video_cutter import main


if __name__ == "__main__":
    main()
