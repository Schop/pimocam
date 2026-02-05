from flask import Flask, jsonify, send_from_directory
from motion_detection import detector
import os

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <h1>Motion Detection Control</h1>
    <a href="/start">Start Motion Detection</a><br>
    <a href="/stop">Stop Motion Detection</a><br>
    <a href="/capture">Manual Capture</a><br>
    <a href="/images">List Images</a>
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
    return jsonify(images)

@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(detector.save_dir, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)