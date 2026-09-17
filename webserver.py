from flask import Flask, send_from_directory, render_template, flash, redirect, url_for
import os
import logging
import shutil
from datetime import datetime
from camera import camera

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'  # Needed for flashing messages

# Disable Flask request logging to reduce spam
log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True


def _list_files(directory, extension):
    items = []
    for f in os.listdir(directory):
        if f.endswith(extension):
            path = os.path.join(directory, f)
            items.append({
                'name': f,
                'size': os.path.getsize(path),
                'mtime': datetime.fromtimestamp(os.path.getmtime(path)),
            })
    items.sort(key=lambda x: x['mtime'], reverse=True)
    return items


@app.route('/')
def index():
    images = _list_files(camera.save_dir, '.jpg')[:25]
    free_space = shutil.disk_usage('/').free / (1024**3)
    return render_template('index.html', images=images, free_space=free_space)


@app.route('/clips')
def clips():
    videos = _list_files(camera.clips_dir, '.mp4')[:25]
    free_space = shutil.disk_usage('/').free / (1024**3)
    return render_template('clips.html', videos=videos, free_space=free_space)


@app.route('/view/<filename>')
def view_image(filename):
    images = sorted([f for f in os.listdir(camera.save_dir) if f.endswith('.jpg')], reverse=True)
    current_index = images.index(filename) if filename in images else -1
    prev_image = images[current_index - 1] if current_index > 0 else None
    next_image = images[current_index + 1] if current_index < len(images) - 1 else None
    return render_template('view.html', filename=filename, prev_image=prev_image, next_image=next_image)


@app.route('/view_clip/<filename>')
def view_clip(filename):
    videos = sorted([f for f in os.listdir(camera.clips_dir) if f.endswith('.mp4')], reverse=True)
    current_index = videos.index(filename) if filename in videos else -1
    prev_video = videos[current_index - 1] if current_index > 0 else None
    next_video = videos[current_index + 1] if current_index < len(videos) - 1 else None
    return render_template('view_clip.html', filename=filename, prev_video=prev_video, next_video=next_video)


@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(camera.save_dir, filename)


@app.route('/clips/<filename>')
def get_clip(filename):
    return send_from_directory(camera.clips_dir, filename)


@app.route('/delete/<filename>', methods=['POST'])
def delete_image(filename):
    try:
        filepath = os.path.join(camera.save_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            flash(f"Deleted {filename}")
        else:
            flash(f"File {filename} not found")
    except Exception as e:
        flash(f"Error deleting {filename}: {str(e)}")
    return redirect(url_for('index'))


@app.route('/delete_clip/<filename>', methods=['POST'])
def delete_clip(filename):
    try:
        filepath = os.path.join(camera.clips_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            flash(f"Deleted {filename}")
        else:
            flash(f"File {filename} not found")
    except Exception as e:
        flash(f"Error deleting {filename}: {str(e)}")
    return redirect(url_for('clips'))


@app.route('/start')
def start():
    try:
        camera.start()
        flash("Motion detection started.")
    except Exception as e:
        flash(f"Failed to start motion detection: {str(e)}")
    return redirect(url_for('index'))


@app.route('/stop')
def stop():
    try:
        camera.stop()
        flash("Motion detection stopped.")
    except Exception as e:
        flash(f"Failed to stop motion detection: {str(e)}")
    return redirect(url_for('index'))


if __name__ == '__main__':
    from settings import WEBSERVER_HOST, WEBSERVER_PORT
    print("Starting camera...")
    camera.start()
    print("Starting webserver...")
    app.run(host=WEBSERVER_HOST, port=WEBSERVER_PORT, debug=False)
