# Raspberry Pi Motion Detection Camera

A Python-based motion detection system for Raspberry Pi with web interface and scheduled captures.

## Features
- Motion-triggered image capture
- Time-based scheduled captures (default: every hour)
- Web interface for control and viewing images
- Configurable save directory via environment variable

## Setup
1. Clone the repository: `git clone https://github.com/Schop/pimocam.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python main.py`

## Configuration
- Edit `settings.py` to customize:
  - Save directory, camera resolutions, motion detection thresholds, scheduler interval, webserver settings
- Set `SAVE_DIR` environment variable to override: `export SAVE_DIR=/path/to/save`

## Web Interface
- Access at `http://your_pi_ip:5000`
- Start/Stop motion detection
- Manual capture
- List and view saved images

## Files
- `main.py`: Entry point
- `motion_detection.py`: Core detection and scheduling logic
- `webserver.py`: Flask web interface
- `settings.py`: Configuration settings
- `requirements.txt`: Dependencies