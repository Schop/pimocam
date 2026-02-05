import os

# Save directory for images
SAVE_DIR = os.getenv('SAVE_DIR', os.path.join(os.path.dirname(__file__), 'pictures'))

# Camera resolutions
MAIN_RES = (2304, 1296)
LORES_RES = (640, 480)

# Motion detection settings
CONTOUR_THRESHOLD = 1000  # Minimum contour area for motion detection
BLUR_KERNEL = (31, 31)  # Gaussian blur kernel size
THRESH_VALUE = 50  # Threshold value for binary threshold
DILATE_ITERATIONS = 2  # Dilate iterations
MOTION_COOLDOWN_SECONDS = 5  # Minimum seconds between motion captures

# Scheduler settings
SCHEDULER_INTERVAL_HOURS = 1  # Hours between scheduled captures

# Webserver settings
WEBSERVER_HOST = '0.0.0.0'
WEBSERVER_PORT = 5000
WEBSERVER_DEBUG = True