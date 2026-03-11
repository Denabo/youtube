from pathlib import Path
from moviepy.editor import VideoFileClip

# 📂 Папки проекта
BASE_DIR = Path(__file__).parent

INPUT_DIR = BASE_DIR / "videos_for_cut"
OUTPUT_DIR = BASE_DIR / "video_cuts"

# ⏱ Тайм-коды нарезки
CUT_RANGES = [
    ("00:00:33", "00:00:58"),
    ("00:00:58", "00:01:51"),
    ("00:01:51", "00:02:49"),
    ("00:02:49", "00:03:49"),
    ("00:03:49", "00:05:37"),
]


def time_to_seconds(time_str: str) -> int:
    h, m, s = map(int, time_str.split(":"))
    return h * 3600 + m * 60 + s


def cut_video(video_path: Path):

    print(f"\n🎬 Найдено видео: {video_path.name}")

    with VideoFileClip(str(video_path)) as video:

        for i, (start_raw, end_raw) in enumerate(CUT_RANGES, 1):

            start = time_to_seconds(start_raw)
            end = time_to_seconds(end_raw)

            clip = video.subclip(start, end)

            output_file = OUTPUT_DIR / f"{video_path.stem}_cut_{i:02d}.mp4"

            print(f"✂️ {start_raw} → {end_raw}  |  {output_file.name}")

            clip.write_videofile(
                str(output_file),
                codec="libx264",
                audio_codec="aac",
                logger=None
            )

    # удаляем исходное видео
    video_path.unlink()
    print(f"🗑 Удалено исходное видео: {video_path.name}")


def main():

    # создаём папки если их нет
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    # поддерживаемые форматы
    video_formats = ["*.mp4", "*.mov", "*.mkv", "*.avi"]

    videos = []

    for fmt in video_formats:
        videos.extend(INPUT_DIR.glob(fmt))

    if not videos:
        print("⚠️ В папке videos_for_cut нет видео")
        return

    for video in videos:
        cut_video(video)

    print("\n✅ Все видео обработаны")


if __name__ == "__main__":
    main()