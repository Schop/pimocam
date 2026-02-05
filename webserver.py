from flask import Flask, jsonify, send_from_directory, render_template, flash, redirect, url_for
from motion_detection import detector
import os
import logging

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'  # Needed for flashing messages

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

@app.route('/capture')
def capture():
    filename = detector.capture_image()
    if filename:
        flash("Image captured successfully!")
    else:
        flash("Failed to capture image.")
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