from flask import Flask, request, jsonify
from moviepy.editor import VideoFileClip
import requests
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "🎥 Video Processor API is running!"

@app.route("/process", methods=["POST"])
def process_video():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing video URL"}), 400

    try:
        filename = "temp_video.mp4"
        with open(filename, "wb") as f:
            f.write(requests.get(url).content)

        clip = VideoFileClip(filename).subclip(0, 5)
        clip.write_videofile("segment_1_video.mp4", codec="libx264")
        os.remove(filename)

        return jsonify({"message": "Video processed"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()
