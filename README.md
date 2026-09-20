# Raspberry Pi Door Camera

A Python-based motion-triggered camera for a Raspberry Pi, watching a front door/driveway. Saves a photo and a short video clip on each motion event, with a web interface for browsing captures.

## Features
- Motion-triggered photo + video clip capture (OpenCV MOG2 background subtraction)
- Configurable ignore zones to exclude parts of the frame (e.g. a plant moving in the wind)
- Web interface for browsing photos and clips
- Configurable save directories via environment variables

## Setup
1. Clone the repository: `git clone https://github.com/Schop/pimocam.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Install ffmpeg (used to encode video clips): `sudo apt install ffmpeg`
4. Run: `python webserver.py`

## Configuration
- Edit `settings.py` to customize save directories, camera resolutions, and motion detection tuning (sensitivity, minimum motion size, cooldown, clip length, ignore zones).
- Set `SAVE_DIR`/`CLIPS_DIR` environment variables to override the default save locations.
- Optional remote backup: set `SFTP_ENABLED=true` plus `SFTP_HOST`, `SFTP_PORT`, `SFTP_USERNAME`, `SFTP_PASSWORD`, and `SFTP_REMOTE_DIR` as environment variables to push every captured photo/clip to a remote SFTP server (files also stay on local disk). Never put these values directly in `settings.py`.

## Web Interface
- Access at `http://your_pi_ip:5000`
- Browse recent photos (`/`) and clips (`/clips`)
- Start/stop motion detection (`/start`, `/stop`)

## Files
- `webserver.py`: Entry point and Flask web interface
- `camera.py`: Camera lifecycle and motion detection/capture logic
- `settings.py`: Configuration settings
- `requirements.txt`: Dependencies
