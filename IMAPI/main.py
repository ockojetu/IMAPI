from flask import Flask, request, send_file, abort
import os
import subprocess
import random
import string

app = Flask(__name__)

def random_filename():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

@app.route('/download', methods=['GET'])
def download():
    yt_url = request.args.get('url')
    if not yt_url:
        return abort(400, "Missing 'url' parameter")

    temp_dir = "/tmp"
    random_id = random_filename()

    video_file = os.path.join(temp_dir, f"video_{random_id}.mp4")
    audio_file = os.path.join(temp_dir, f"audio_{random_id}.m4a")
    output_file = os.path.join(temp_dir, f"output_{random_id}.mp4")

    ydl_opts = {'quiet': True, 'no_warnings': True}

    from yt_dlp import YoutubeDL

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(yt_url, download=False)

        video_formats = [f for f in info['formats'] if f.get('vcodec') != 'none' and f.get('acodec') == 'none' and 'hls' not in f.get('protocol', '')]
        audio_formats = [f for f in info['formats'] if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and 'hls' not in f.get('protocol', '')]

        best_video = max(video_formats, key=lambda f: f.get('height') or 0)
        best_audio = max(audio_formats, key=lambda f: f.get('abr') or 0)

        video_url = best_video['url']
        audio_url = best_audio['url']

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

        return send_file(output_file, as_attachment=True, download_name="downloaded_video.mp4")

    except Exception as e:
        return f"Error: {e}", 500
    finally:
        if os.path.exists(video_file):
            os.remove(video_file)
        if os.path.exists(audio_file):
            os.remove(audio_file)
        if os.path.exists(output_file):
            os.remove(output_file)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
