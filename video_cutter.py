"""
Нарезка видео по списку тайм-кодов.

Примеры:
1) Использовать список прямо в коде (CUT_RANGES)
   python video_cutter.py --input input/source/my_video.mp4 --output output/cuts

2) Использовать файл диапазонов
   python video_cutter.py --input input/source/my_video.mp4 --output output/cuts --ranges-file cuts.txt

Формат cuts.txt (по строке):
start,end,name
00:00:05,00:00:15,intro
00:00:30,00:00:42,hook
01:10,01:25,
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Tuple

# Можно редактировать вручную
CUT_RANGES: List[Tuple[str, str, str]] = [
    ("00:00:00", "00:00:10", "part_01"),
    ("00:00:10", "00:00:20", "part_02"),
]


def time_to_seconds(value: str) -> int:
    parts = [int(x) for x in value.strip().split(":")]
    if len(parts) == 3:
        h, m, s = parts
        return h * 3600 + m * 60 + s
    if len(parts) == 2:
        m, s = parts
        return m * 60 + s
    if len(parts) == 1:
        return parts[0]
    raise ValueError(f"Некорректный формат времени: {value}")


def parse_ranges_file(path: Path) -> List[Tuple[str, str, str]]:
    ranges: List[Tuple[str, str, str]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower() in {"start,end", "start,end,name"}:
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 2:
            raise ValueError(f"Неверная строка: {line}")
        start, end = parts[0], parts[1]
        name = parts[2] if len(parts) >= 3 and parts[2] else ""
        ranges.append((start, end, name))
    return ranges


def cut_video_by_ranges(input_path: Path, output_dir: Path, ranges: Iterable[Tuple[str, str, str]]) -> None:
    from moviepy.editor import VideoFileClip

    output_dir.mkdir(parents=True, exist_ok=True)

    with VideoFileClip(str(input_path)) as video:
        for index, (start_raw, end_raw, name) in enumerate(ranges, 1):
            start = time_to_seconds(start_raw)
            end = time_to_seconds(end_raw)

            if end <= start:
                raise ValueError(f"Конец должен быть больше начала: {start_raw} - {end_raw}")
            if start >= video.duration:
                raise ValueError(f"Начало отрезка вне видео: {start_raw}")

            safe_end = min(end, video.duration)
            chunk = video.subclip(start, safe_end)

            suffix = name if name else f"part_{index:02d}"
            output_path = output_dir / f"{input_path.stem}_{suffix}.mp4"
            print(f"✂️  {start_raw} - {end_raw} -> {output_path.name}")
            chunk.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                logger=None,
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Нарезка видео по списку тайм-кодов")
    parser.add_argument("--input", required=True, help="Путь к исходному видео")
    parser.add_argument("--output", required=True, help="Папка для сохранения нарезок")
    parser.add_argument("--ranges-file", help="Файл со списком диапазонов start,end,name")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)

    ranges = CUT_RANGES
    if args.ranges_file:
        ranges = parse_ranges_file(Path(args.ranges_file))

    cut_video_by_ranges(input_path, output_dir, ranges)


if __name__ == "__main__":
    main()
