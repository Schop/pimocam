from flask import Flask, jsonify, send_from_directory, render_template, flash, redirect, url_for, request
import importlib
import sys
import re
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

# Helper to load settings as dict
def load_settings():
    import settings
    # Only show editable settings (not imported modules, etc.)
    keys = [k for k in dir(settings) if k.isupper() and not k.startswith('__')]
    return {k: getattr(settings, k) for k in keys}

# Helper to update settings.py file
def update_settings(new_settings):
    settings_path = os.path.join(os.path.dirname(__file__), 'settings.py')
    with open(settings_path, 'r') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        m = re.match(r'^(\w+)\s*=\s*(.+)', line)
        if m:
            key = m.group(1)
            if key in new_settings:
                val = new_settings[key]
                # Try to keep type (int/float/str/tuple)
                if val.isdigit():
                    val_str = val
                else:
                    try:
                        float(val)
                        val_str = val
                    except:
                        if val.startswith('(') and val.endswith(')'):
                            val_str = val
                        else:
                            val_str = f'"{val}"'
                lines[i] = f'{key} = {val_str}\n'
    with open(settings_path, 'w') as f:
        f.writelines(lines)

# Settings page (GET: view, POST: update)
@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    message = None
    readonly = ['SAVE_DIR', 'TIME_LAPSE_DIR']
    if request.method == 'POST':
        # Only update editable settings
        editable = [k for k in load_settings().keys() if k not in readonly]
        new_settings = {k: request.form[k] for k in editable if k in request.form}
        update_settings(new_settings)
        # Reload settings module
        if 'settings' in sys.modules:
            importlib.reload(sys.modules['settings'])
        message = 'Settings updated!'
    settings_dict = load_settings()
    return render_template('settings.html', settings=settings_dict, readonly=readonly, message=message)



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

@app.route('/view/<filename>')
def view_image(filename):
    return render_template('view.html', filename=filename)

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