from moviepy.editor import VideoFileClip


def cut_video(input_path, output_path, start_time, end_time):

    # Загружаем видео
    video = VideoFileClip(input_path)

    # Конвертируем время в секунды
    def time_to_seconds(t):
        parts = list(map(int, t.split(':')))
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return int(parts[0])

    start = time_to_seconds(start_time)
    end = time_to_seconds(end_time)

    # Обрезаем
    cut = video.subclip(start, end)

    # Сохраняем результат
    cut.write_videofile(output_path, codec='libx264', audio_codec='aac')


# 🔹 Пример использования
if __name__ == "__main__":
    cut_video(
        input_path= r"C:\Users\hhdjd\PycharmProject\youtue\output\shorts_final.mp4",
        output_path= r"C:\Users\hhdjd\PycharmProject\youtue\output\shorts_final_СГЕ.mp4",
        start_time="00:00:00",
        end_time="00:00:59"
    )
