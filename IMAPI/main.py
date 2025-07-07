import os
import subprocess
import random
import string
from flask import Flask, request, jsonify
from yt_dlp import YoutubeDL

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def random_filename():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    output_file = os.path.join(DOWNLOAD_DIR, f"finished_{random_filename()}.mp4")

    ydl_opts = {'quiet': True, 'no_warnings': True}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        video_formats = [f for f in info['formats'] if f.get('vcodec') != 'none' and f.get('acodec') == 'none' and 'hls' not in f.get('protocol', '')]
        audio_formats = [f for f in info['formats'] if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and 'hls' not in f.get('protocol', '')]

        best_video = max(video_formats, key=lambda f: f.get('height') or 0)
        best_audio = max(audio_formats, key=lambda f: f.get('abr') or 0)

        video_url = best_video['url']
        audio_url = best_audio['url']

        video_file = os.path.join(DOWNLOAD_DIR, f"video_{random_filename()}.mp4")
        audio_file = os.path.join(DOWNLOAD_DIR, f"audio_{random_filename()}.m4a")

        subprocess.run(['ffmpeg', '-y', '-i', video_url, '-c', 'copy', video_file], check=True)
        subprocess.run(['ffmpeg', '-y', '-i', audio_url, '-c:a', 'aac', '-b:a', '192k', audio_file], check=True)

        subprocess.run([
            'ffmpeg', '-y',
            '-i', video_file,
            '-i', audio_file,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            output_file
        ], check=True)

        os.remove(video_file)
        os.remove(audio_file)

        return jsonify({"status": "success", "file": output_file})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
