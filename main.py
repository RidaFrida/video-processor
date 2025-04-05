from flask import Flask, request, jsonify, send_from_directory
from moviepy.editor import VideoFileClip
import os
import requests
import tempfile

app = Flask(__name__)
OUTPUT_DIR = "segments"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route("/")
def home():
    return "🎬 Video Processor is running!"

@app.route("/process", methods=["POST"])
def process_video():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing video URL"}), 400

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(requests.get(url).content)
            tmp_path = tmp.name

        clip = VideoFileClip(tmp_path)
        duration = int(clip.duration)
        segment_count = duration // 5

        saved_files = []

        # Сохраняем всё аудио
        full_audio = "full_audio.mp3"
        full_audio_path = os.path.join(OUTPUT_DIR, full_audio)
        clip.audio.write_audiofile(full_audio_path, verbose=False, logger=None)
        saved_files.append(full_audio)

        # Сохраняем фрагменты
        for i in range(segment_count):
            start = i * 5
            end = min((i + 1) * 5, duration)
            subclip = clip.subclip(start, end)

            if i % 2 == 0:
                fname = f"video_{i+1}.mp4"
                subclip.write_videofile(os.path.join(OUTPUT_DIR, fname), codec="libx264", audio_codec="aac", verbose=False, logger=None)
            else:
                fname = f"audio_{i+1}.mp3"
                subclip.audio.write_audiofile(os.path.join(OUTPUT_DIR, fname), verbose=False, logger=None)

            saved_files.append(fname)

        clip.close()
        os.remove(tmp_path)

        base_url = request.host_url.rstrip("/") + "/download"
        download_links = [f"{base_url}/{f}" for f in saved_files]

        return jsonify({"message": "✅ Done", "links": download_links})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download/<path:filename>")
def download(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)
