import cv2
import numpy as np
from picamera2 import Picamera2
import time
import os
import threading
import shutil
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
from settings import SAVE_DIR, MAIN_RES, LORES_RES, TIME_LAPSE_DIR
from db_settings import get_setting

def cleanup_old_files(directory, min_free_gb=None):
    """Delete oldest files in directory if free disk space is below min_free_gb"""
    if min_free_gb is None:
        min_free_gb = get_setting('MIN_FREE_GB', 10.0)
    free_gb = shutil.disk_usage('/').free / (1024**3)
    if free_gb < min_free_gb:
        files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.jpg')]
        files.sort(key=os.path.getmtime)  # Oldest first
        while files and free_gb < min_free_gb:
            oldest = files.pop(0)
            try:
                os.remove(oldest)
                print(f"Deleted old file: {oldest}")
                free_gb = shutil.disk_usage('/').free / (1024**3)
            except OSError as e:
                print(f"Error deleting {oldest}: {e}")

def sync_to_gdrive():
    try:
        # Sync pictures
        result1 = subprocess.run(['rclone', 'sync', SAVE_DIR, 'GDrive:/PiMotion/pictures', '--log-level', 'INFO'], check=True)
        # Sync timelapse
        result2 = subprocess.run(['rclone', 'sync', TIME_LAPSE_DIR, 'GDrive:/PiMotion/timelapse', '--log-level', 'INFO'], check=True)
        print("Synced to Google Drive")
    except subprocess.CalledProcessError as e:
        print(f"Sync error: {e}")
    except Exception as e:
        print(f"Sync error: {e}")

class MotionDetector:
    def __init__(self):
        self.picam2 = None
        self.running = False
        self.save_dir = SAVE_DIR
        os.makedirs(self.save_dir, exist_ok=True)
        self.timelapse_dir = TIME_LAPSE_DIR
        os.makedirs(self.timelapse_dir, exist_ok=True)
        self.frame1 = None
        self.thread = None
        self.last_capture = 0

    def start(self):
        if self.running:
            return
        self.running = True
        try:
            self.picam2 = Picamera2()
            config = self.picam2.create_preview_configuration(main={"size": MAIN_RES, "format": "RGB888"}, lores={"size": LORES_RES})
            self.picam2.configure(config)
            self.picam2.start()
            time.sleep(2)
            # Capture first frame
            frame1_yuv = self.picam2.capture_array("lores")
            frame1_color = cv2.cvtColor(frame1_yuv, cv2.COLOR_YUV2RGB_I420)
            self.frame1 = cv2.cvtColor(frame1_color, cv2.COLOR_BGR2GRAY)
            blur_size = get_setting('BLUR_KERNEL', 15)
            self.frame1 = cv2.GaussianBlur(self.frame1, (blur_size, blur_size), 0)
            print("Motion detection started.")
            self.thread = threading.Thread(target=self._detect_loop)
            self.thread.start()
        except RuntimeError as e:
            print(f"Failed to start camera: {e}")
            self.running = False

    def stop(self):
        self.running = False
        if self.picam2:
            self.picam2.stop()
        if self.thread:
            self.thread.join()
        print("Motion detection stopped.")

    def _detect_loop(self):
        while self.running:
            # Get current settings
            blur_size = get_setting('BLUR_KERNEL', 15)
            thresh_value = get_setting('THRESH_VALUE', 35)
            dilate_iterations = get_setting('DILATE_ITERATIONS', 2)
            contour_threshold = get_setting('CONTOUR_THRESHOLD', 300)
            cooldown = get_setting('MOTION_COOLDOWN_SECONDS', 5)
            
            # Capture current frame
            frame2_yuv = self.picam2.capture_array("lores")
            frame2_color = cv2.cvtColor(frame2_yuv, cv2.COLOR_YUV2RGB_I420)
            frame2 = cv2.cvtColor(frame2_color, cv2.COLOR_BGR2GRAY)
            frame2 = cv2.GaussianBlur(frame2, (blur_size, blur_size), 0)
            # Compute the absolute difference
            frame_diff = cv2.absdiff(self.frame1, frame2)
            thresh = cv2.threshold(frame_diff, thresh_value, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=dilate_iterations)
            # Find contours
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            motion_detected = any(cv2.contourArea(contour) > contour_threshold for contour in contours)
            if motion_detected:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = os.path.join(self.save_dir, f"motion_{timestamp}.jpg")
                cv2.imwrite(filename, self.picam2.capture_array("main"))
                print(f"Motion detected! Image saved as {filename}")
                time.sleep(cooldown)
            self.frame1 = frame2
            time.sleep(0.1)

    def capture_image(self):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.save_dir, f"capture_{timestamp}.jpg")
        if self.picam2:
            self.picam2.capture_file(filename)
            print(f"Image captured: {filename}")
            cleanup_old_files(self.save_dir)
            return filename
        else:
            print("Camera not initialized")
            return None

    def capture_timelapse(self):
        brightness_threshold = get_setting('TIMELAPSE_BRIGHTNESS_THRESHOLD', 40)
        print("Timelapse job triggered")
        # Grab a low-res frame and check brightness
        if self.picam2:
            try:
                preview_yuv = self.picam2.capture_array("lores")
                preview_color = cv2.cvtColor(preview_yuv, cv2.COLOR_YUV2RGB_I420)
                preview_gray = cv2.cvtColor(preview_color, cv2.COLOR_BGR2GRAY)
                mean_brightness = np.mean(preview_gray)
                print(f"Timelapse brightness: {mean_brightness:.1f} (threshold: {brightness_threshold})")
                if mean_brightness < brightness_threshold:
                    print(f"Too dark for timelapse, skipping.")
                    return None
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = os.path.join(self.timelapse_dir, f"timelapse_{timestamp}.jpg")
                self.picam2.capture_file(filename)
                print(f"Timelapse captured: {filename}")
                cleanup_old_files(self.timelapse_dir)
                return filename
            except Exception as e:
                print(f"Error capturing timelapse: {e}")
                return None
        else:
            print("Camera not initialized for timelapse")
            return None

# Global instances
detector = MotionDetector()
scheduler = BackgroundScheduler()

def main():
    detector.start()
    interval_minutes = get_setting('SCHEDULER_INTERVAL_MINUTES', 30)
    scheduler.add_job(func=lambda: detector.capture_timelapse(), trigger="interval", minutes=interval_minutes)
    scheduler.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        detector.stop()
        scheduler.shutdown()

if __name__ == "__main__":
    main()