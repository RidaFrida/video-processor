from flask import Flask, request, jsonify, send_from_directory
import os
import requests
import ffmpeg
import math
from uuid import uuid4

app = Flask(__name__)
os.makedirs("outputs", exist_ok=True)

@app.route("/")
def home():
    return "🎬 Video Processor is running!"

@app.route("/process", methods=["POST"])
def process_video():
    try:
        data = request.get_json()
        url = data.get("url")
        if not url:
            return jsonify({"error": "Missing video URL"}), 400

        # Скачиваем видео
        uid = str(uuid4())
        video_path = f"outputs/{uid}.mp4"
        r = requests.get(url, stream=True)
        with open(video_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # Извлекаем общее аудио
        full_audio_path = f"outputs/{uid}_full_audio.mp3"
        ffmpeg.input(video_path).output(full_audio_path).run(overwrite_output=True)

        # Получаем длительность видео
        probe = ffmpeg.probe(video_path)
        duration = float(probe["format"]["duration"])
        segments = math.ceil(duration / 5)

        audio_links = []
        video_links = []

        for i in range(segments):
            start = i * 5
            segment_id = f"{uid}_segment_{i+1}"

            if (i + 1) % 2 == 0:
                # Чётные — извлекаем аудио
                audio_out = f"outputs/{segment_id}_audio.mp3"
                ffmpeg.input(video_path, ss=start, t=5).output(audio_out).run(overwrite_output=True)
                audio_links.append(f"/download/{os.path.basename(audio_out)}")
            else:
                # Нечётные — извлекаем видео
                video_out = f"outputs/{segment_id}_video.mp4"
                ffmpeg.input(video_path, ss=start, t=5).output(video_out).run(overwrite_output=True)
                video_links.append(f"/download/{os.path.basename(video_out)}")

        # Удаляем исходное видео
        os.remove(video_path)

        return jsonify({
            "full_audio": f"/download/{os.path.basename(full_audio_path)}",
            "audio_segments": audio_links,
            "video_segments": video_links
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory("outputs", filename, as_attachment=True)

if __name__ == "__main__":
    app.run()
