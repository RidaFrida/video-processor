from flask import Flask, request, jsonify, send_file
import os
import requests
import ffmpeg

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Video Processor API is running!"

@app.route("/process", methods=["POST"])
def process_video():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing video URL"}), 400

    try:
        # 1. Скачать видео
        video_path = "temp_video.mp4"
        r = requests.get(url)
        with open(video_path, "wb") as f:
            f.write(r.content)

        # 2. Извлечь всё аудио
        audio_full = "full_audio.wav"
        ffmpeg.input(video_path).output(audio_full).run(overwrite_output=True)

        # 3. Разбить видео на сегменты и сохранить аудио / видео
        probe = ffmpeg.probe(video_path)
        duration = float(probe['format']['duration'])
        segment_duration = 5
        i = 0
        segment_index = 1

        while i < duration:
            segment_start = i
            segment_end = min(i + segment_duration, duration)

            if segment_index % 2 == 0:
                # Четные: аудио
                audio_out = f"segment_{segment_index}_audio.wav"
                ffmpeg.input(video_path, ss=segment_start, t=segment_duration)\
                      .output(audio_out).run(overwrite_output=True)
            else:
                # Нечетные: видео
                video_out = f"segment_{segment_index}_video.mp4"
                ffmpeg.input(video_path, ss=segment_start, t=segment_duration)\
                      .output(video_out).run(overwrite_output=True)

            i += segment_duration
            segment_index += 1

        return jsonify({
            "message": "✔ Обработка завершена",
            "download": {
                "full_audio": "/download/full_audio.wav"
            }
        })

  
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    except ffmpeg.Error as e:
        error_message = e.stderr.decode() if e.stderr else str(e)
        return jsonify({"error": "FFmpeg error", "details": error_message}), 500

@app.route('/download/<filename>')
def download_file(filename):
    path = os.path.join(".", filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404

if __name__ == "__main__":
    app.run()
