from flask import Flask, jsonify, send_from_directory
from motion_detection import detector
import os
import logging

app = Flask(__name__)

# Disable Flask request logging to reduce spam
log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Motion Detection Control</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h1 class="mb-4">Motion Detection Control</h1>
            <div class="row">
                <div class="col-md-6">
                    <a href="/start" class="btn btn-success btn-lg mb-3">Start Motion Detection</a><br>
                    <a href="/stop" class="btn btn-danger btn-lg mb-3">Stop Motion Detection</a><br>
                    <a href="/capture" class="btn btn-primary btn-lg mb-3">Manual Capture</a><br>
                    <a href="/images" class="btn btn-info btn-lg">View Images</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

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
    html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Images</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h1 class="mb-4">Captured Images</h1>
            <a href="/" class="btn btn-secondary mb-4">Back to Control</a>
            <div class="row">
    '''
    for img in images:
        html += f'''
                <div class="col-md-3 mb-3">
                    <div class="card">
                        <a href="/images/{img}">
                            <img src="/images/{img}" class="card-img-top" style="height: 200px; object-fit: cover;">
                        </a>
                        <div class="card-body">
                            <p class="card-text">{img}</p>
                        </div>
                    </div>
                </div>
        '''
    html += '''
            </div>
        </div>
    </body>
    </html>
    '''
    return html

@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(detector.save_dir, filename)