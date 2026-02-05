from flask import Flask, jsonify, send_from_directory, render_template, flash, redirect, url_for
from motion_detection import detector
import os
import logging
import shutil
from datetime import datetime

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'  # Needed for flashing messages

# Disable Flask request logging to reduce spam
log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True

app = Flask(__name__)

@app.route('/')
def index():
    save_dir = detector.save_dir
    images = []
    for f in os.listdir(save_dir):
        if f.endswith('.jpg'):
            path = os.path.join(save_dir, f)
            size = os.path.getsize(path)
            mtime = os.path.getmtime(path)
            mtime_dt = datetime.fromtimestamp(mtime)
            images.append({'name': f, 'size': size, 'mtime': mtime_dt})
    images.sort(key=lambda x: x['mtime'], reverse=True)  # Newest first
    free_space = shutil.disk_usage('/').free / (1024**3)  # Free space in GB
    return render_template('index.html', images=images, free_space=free_space)

@app.route('/timelapse')
def timelapse():
    save_dir = detector.timelapse_dir
    images = []
    for f in os.listdir(save_dir):
        if f.endswith('.jpg'):
            path = os.path.join(save_dir, f)
            size = os.path.getsize(path)
            mtime = os.path.getmtime(path)
            mtime_dt = datetime.fromtimestamp(mtime)
            images.append({'name': f, 'size': size, 'mtime': mtime_dt})
    images.sort(key=lambda x: x['mtime'], reverse=True)
    free_space = shutil.disk_usage('/').free / (1024**3)  # Free space in GB
    return render_template('timelapse.html', images=images, free_space=free_space)

@app.route('/timelapse/<filename>')
def view_timelapse_image(filename):
    return render_template('view_timelapse.html', filename=filename)

@app.route('/timelapse_image/<filename>')
def get_timelapse_image(filename):
    return send_from_directory(detector.timelapse_dir, filename)

@app.route('/start')
def start():
    try:
        detector.start()
        flash("Motion detection started.")
    except Exception as e:
        flash(f"Failed to start motion detection: {str(e)}")
    return redirect(url_for('index'))

@app.route('/stop')
def stop():
    try:
        detector.stop()
        flash("Motion detection stopped.")
    except Exception as e:
        flash(f"Failed to stop motion detection: {str(e)}")
    return redirect(url_for('index'))

@app.route('/images')
def list_images():
    save_dir = detector.save_dir
    images = [f for f in os.listdir(save_dir) if f.endswith('.jpg')]
    images.sort(reverse=True)  # Sort by name descending (newest first, assuming timestamped names)
    return render_template('images.html', images=images)

@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(detector.save_dir, filename)

if __name__ == '__main__':
    from motion_detection import scheduler
    from settings import WEBSERVER_HOST, WEBSERVER_PORT, WEBSERVER_DEBUG, SCHEDULER_INTERVAL_MINUTES
    print("Starting detector...")
    detector.start()
    print("Adding timelapse job...")
    scheduler.add_job(func=lambda: detector.capture_timelapse(), trigger="interval", minutes=SCHEDULER_INTERVAL_MINUTES)
    print("Starting scheduler...")
    scheduler.start()
    print("Starting webserver...")
    app.run(host=WEBSERVER_HOST, port=WEBSERVER_PORT, debug=WEBSERVER_DEBUG)