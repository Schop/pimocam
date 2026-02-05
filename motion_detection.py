import cv2
import numpy as np
from picamera2 import Picamera2
import time
import os
import threading
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
from settings import SAVE_DIR, MAIN_RES, LORES_RES, CONTOUR_THRESHOLD, BLUR_KERNEL, THRESH_VALUE, DILATE_ITERATIONS, SCHEDULER_INTERVAL_HOURS, TIME_LAPSE_DIR, MOTION_COOLDOWN_SECONDS

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
            self.frame1 = cv2.GaussianBlur(self.frame1, BLUR_KERNEL, 0)
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
            # Capture current frame
            frame2_yuv = self.picam2.capture_array("lores")
            frame2_color = cv2.cvtColor(frame2_yuv, cv2.COLOR_YUV2RGB_I420)
            frame2 = cv2.cvtColor(frame2_color, cv2.COLOR_BGR2GRAY)
            frame2 = cv2.GaussianBlur(frame2, BLUR_KERNEL, 0)
            # Compute the absolute difference
            frame_diff = cv2.absdiff(self.frame1, frame2)
            thresh = cv2.threshold(frame_diff, THRESH_VALUE, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=DILATE_ITERATIONS)
            # Find contours
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            motion_detected = any(cv2.contourArea(contour) > CONTOUR_THRESHOLD for contour in contours)
            if motion_detected:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = os.path.join(self.save_dir, f"motion_{timestamp}.jpg")
                cv2.imwrite(filename, self.picam2.capture_array("main"))
                print(f"Motion detected! Image saved as {filename}")
                time.sleep(5)
            self.frame1 = frame2
            time.sleep(0.1)

    def capture_image(self):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.save_dir, f"capture_{timestamp}.jpg")
        # Use rpicam-still for capture to avoid interfering with motion detection
        subprocess.run(['rpicam-still', '-o', filename, '--width', str(MAIN_RES[0]), '--height', str(MAIN_RES[1])])
        print(f"Image captured: {filename}")
        return filename

    def capture_timelapse(self):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.timelapse_dir, f"timelapse_{timestamp}.jpg")
        if self.picam2:
            self.picam2.capture_file(filename)
            print(f"Timelapse captured: {filename}")
            return filename
        else:
            print("Camera not initialized for timelapse")
            return None

# Global instances
detector = MotionDetector()
scheduler = BackgroundScheduler()

# Scheduled capture
scheduler.add_job(func=lambda: detector.capture_timelapse(), trigger="interval", hours=SCHEDULER_INTERVAL_HOURS)
scheduler.start()

def main():
    detector.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        detector.stop()
        scheduler.shutdown()

if __name__ == "__main__":
    main()