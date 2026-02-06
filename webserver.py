from flask import Flask, jsonify, send_from_directory, render_template, flash, redirect, url_for, request
import importlib
import sys
import re
from motion_detection import detector
import os
import logging
import shutil
from datetime import datetime
from db_settings import get_all_settings, get_settings_by_category, get_setting, set_setting, reset_to_defaults

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'  # Needed for flashing messages

# Disable Flask request logging to reduce spam
log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True

# API: Get all settings
@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    """Get all settings organized by category"""
    try:
        settings = get_settings_by_category()
        return jsonify({'success': True, 'settings': settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API: Update a setting
@app.route('/api/settings/<key>', methods=['POST'])
def api_update_setting(key):
    """Update a single setting"""
    try:
        data = request.get_json()
        value = data.get('value')
        if value is None:
            return jsonify({'success': False, 'error': 'Missing value'}), 400
        set_setting(key, value)
        return jsonify({'success': True, 'message': f'{key} updated successfully'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API: Reset all settings to defaults
@app.route('/api/settings/reset', methods=['POST'])
def api_reset_settings():
    """Reset all settings to default values"""
    try:
        reset_to_defaults()
        return jsonify({'success': True, 'message': 'All settings reset to defaults'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Settings page
@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    message = None
    message_type = 'success'
    
    if request.method == 'POST':
        try:
            # Check if this is a reset request
            if 'reset' in request.form:
                reset_to_defaults()
                message = 'All settings reset to defaults!'
            else:
                # Update individual settings
                for key, value in request.form.items():
                    if key != 'csrf_token':  # Skip CSRF token if present
                        try:
                            set_setting(key, value)
                        except ValueError as e:
                            message = f'Error updating {key}: {str(e)}'
                            message_type = 'error'
                            break
                else:
                    message = 'Settings updated successfully!'
        except Exception as e:
            message = f'Error: {str(e)}'
            message_type = 'error'
    
    settings_dict = get_settings_by_category()
    return render_template('settings.html', settings=settings_dict, message=message, message_type=message_type)



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
    # Get all timelapse images sorted by name (newest first)
    images = sorted([f for f in os.listdir(detector.timelapse_dir) if f.endswith('.jpg')], reverse=True)
    current_index = images.index(filename) if filename in images else -1
    prev_image = images[current_index - 1] if current_index > 0 else None
    next_image = images[current_index + 1] if current_index < len(images) - 1 else None
    return render_template('view_timelapse.html', filename=filename, prev_image=prev_image, next_image=next_image)

@app.route('/timelapse_image/<filename>')
def get_timelapse_image(filename):
    return send_from_directory(detector.timelapse_dir, filename)

@app.route('/view/<filename>')
def view_image(filename):
    # Get all motion images sorted by name (newest first)
    images = sorted([f for f in os.listdir(detector.save_dir) if f.endswith('.jpg')], reverse=True)
    current_index = images.index(filename) if filename in images else -1
    prev_image = images[current_index - 1] if current_index > 0 else None
    next_image = images[current_index + 1] if current_index < len(images) - 1 else None
    return render_template('view.html', filename=filename, prev_image=prev_image, next_image=next_image)

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
    from settings import WEBSERVER_HOST
    from db_settings import get_setting
    print("Starting detector...")
    detector.start()
    print("Adding timelapse job...")
    interval_minutes = get_setting('SCHEDULER_INTERVAL_MINUTES', 30)
    scheduler.add_job(func=lambda: detector.capture_timelapse(), trigger="interval", minutes=interval_minutes)
    print("Starting scheduler...")
    scheduler.start()
    print("Starting webserver...")
    port = get_setting('WEBSERVER_PORT', 5000)
    debug = get_setting('WEBSERVER_DEBUG', True)
    app.run(host=WEBSERVER_HOST, port=port, debug=debug)