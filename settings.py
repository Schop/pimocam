import os

# Save directories
SAVE_DIR = os.getenv('SAVE_DIR', os.path.join(os.path.dirname(__file__), 'pictures'))
CLIPS_DIR = os.getenv('CLIPS_DIR', os.path.join(os.path.dirname(__file__), 'clips'))

# Camera resolutions
MAIN_RES = (1640, 1232)
LORES_RES = (640, 480)
RECORDING_FPS = 15  # Fixed capture rate; must match what the encoder assumes or clips play at the wrong duration

# Motion detection settings
CONTOUR_THRESHOLD = 800  # Minimum contour area for motion detection (people/animals/cars, not small birds)
BLUR_KERNEL = 15  # Gaussian blur kernel size (must be odd)
THRESH_VALUE = 40  # Sensitivity of the background model (MOG2 varThreshold)
DILATE_ITERATIONS = 2  # Dilate iterations
MOTION_COOLDOWN_SECONDS = 5  # Minimum seconds between motion captures
MOTION_CLIP_SECONDS = 8  # Length of the video clip recorded on each motion trigger

# Rectangles to exclude from motion detection, in the 640x480 low-res frame: (x1, y1, x2, y2).
# Useful for things like a wind-blown plant or flag that keeps falsely triggering captures.
MOTION_IGNORE_ZONES = []

# Disk cleanup settings
MIN_FREE_GB = 10.0  # Minimum free disk space in GB before deleting old files

# Webserver settings
WEBSERVER_HOST = '0.0.0.0'
WEBSERVER_PORT = 5000
