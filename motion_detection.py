import cv2
import numpy as np
from picamera2 import Picamera2
import time
import os
import threading
from apscheduler.schedulers.background import BackgroundScheduler

class MotionDetector:
    def __init__(self):
        self.picam2 = None
        self.running = False
        self.save_dir = os.getenv('SAVE_DIR', '/home/schop/Pictures')
        os.makedirs(self.save_dir, exist_ok=True)
        self.frame1 = None
        self.thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(main={"size": (2304, 1296), "format": "RGB888"}, lores={"size": (640, 480)})
        self.picam2.configure(config)
        self.picam2.start()
        time.sleep(2)
        # Capture first frame
        frame1_yuv = self.picam2.capture_array("lores")
        frame1_color = cv2.cvtColor(frame1_yuv, cv2.COLOR_YUV2RGB_I420)
        self.frame1 = cv2.cvtColor(frame1_color, cv2.COLOR_BGR2GRAY)
        self.frame1 = cv2.GaussianBlur(self.frame1, (31, 31), 0)
        print("Motion detection started.")
        self.thread = threading.Thread(target=self._detect_loop)
        self.thread.start()

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
            frame2 = cv2.GaussianBlur(frame2, (31, 31), 0)
            # Compute the absolute difference
            frame_diff = cv2.absdiff(self.frame1, frame2)
            thresh = cv2.threshold(frame_diff, 50, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            # Find contours
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            motion_detected = any(cv2.contourArea(contour) > 1000 for contour in contours)
            if motion_detected:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = os.path.join(self.save_dir, f"motion_{timestamp}.jpg")
                cv2.imwrite(filename, self.picam2.capture_array("main"))
                print(f"Motion detected! Image saved as {filename}")
                time.sleep(5)
            self.frame1 = frame2
            time.sleep(0.1)

    def capture_image(self):
        if not self.picam2:
            return None
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.save_dir, f"capture_{timestamp}.jpg")
        cv2.imwrite(filename, self.picam2.capture_array("main"))
        print(f"Image captured: {filename}")
        return filename

# Global instances
detector = MotionDetector()
scheduler = BackgroundScheduler()

# Example: Capture every hour
scheduler.add_job(func=lambda: detector.capture_image(), trigger="interval", hours=1)
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