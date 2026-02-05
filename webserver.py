from flask import Flask, jsonify, send_from_directory, render_template
from motion_detection import detector
import os
import logging

app = Flask(__name__, template_folder='templates')

# Disable Flask request logging to reduce spam
log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start')
def start():
    detector.start()
    return "Motion detection started."

@app.route('/stop')
def stop():
    detector.stop()
    return "Motion detection stopped."

@app.route('/capture')
def capture():
    filename = detector.capture_image()
    if filename:
        return jsonify({"message": "Image captured", "filename": filename})
    return "Camera not initialized."

@app.route('/images')
def list_images():
    save_dir = detector.save_dir
    images = [f for f in os.listdir(save_dir) if f.endswith('.jpg')]
    images.sort(reverse=True)  # Sort by name descending (newest first, assuming timestamped names)
    return render_template('images.html', images=images)

@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(detector.save_dir, filename)