import cv2
import numpy as np
import time
import os
import threading
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
from settings import SAVE_DIR, MAIN_RES, LORES_RES, CONTOUR_THRESHOLD, BLUR_KERNEL, THRESH_VALUE, DILATE_ITERATIONS, SCHEDULER_INTERVAL_HOURS

class MotionDetector:
    def __init__(self):
        self.cap = None
        self.running = False
        self.save_dir = SAVE_DIR
        os.makedirs(self.save_dir, exist_ok=True)
        self.frame1 = None
        self.thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.cap = cv2.VideoCapture(0)  # Use default camera
        if not self.cap.isOpened():
            print("Error: Could not open camera.")
            self.running = False
            return
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, LORES_RES[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, LORES_RES[1])
        time.sleep(2)
        # Capture first frame
        ret, frame = self.cap.read()
        if ret:
            self.frame1 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.frame1 = cv2.GaussianBlur(self.frame1, BLUR_KERNEL, 0)
        else:
            print("Error: Could not read frame.")
            self.running = False
            return
        print("Motion detection started.")
        self.thread = threading.Thread(target=self._detect_loop)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        if self.thread:
            self.thread.join()
        print("Motion detection stopped.")

    def _detect_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue
            frame2 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
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
                # Use rpicam-still for high-res capture
                subprocess.run(['rpicam-still', '-o', filename, '--width', str(MAIN_RES[0]), '--height', str(MAIN_RES[1])])
                print(f"Motion detected! Image saved as {filename}")
                time.sleep(5)
            self.frame1 = frame2
            time.sleep(0.1)

    def capture_image(self):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.save_dir, f"capture_{timestamp}.jpg")
        # Use rpicam-still for capture
        subprocess.run(['rpicam-still', '-o', filename, '--width', str(MAIN_RES[0]), '--height', str(MAIN_RES[1])])
        print(f"Image captured: {filename}")
        return filename

# Global instances
detector = MotionDetector()
scheduler = BackgroundScheduler()

# Scheduled capture
scheduler.add_job(func=lambda: detector.capture_image(), trigger="interval", hours=SCHEDULER_INTERVAL_HOURS)
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