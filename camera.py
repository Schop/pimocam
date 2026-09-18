import cv2
import time
import os
import threading
import shutil
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput
from settings import (
    SAVE_DIR, CLIPS_DIR, MAIN_RES, LORES_RES, RECORDING_FPS,
    CONTOUR_THRESHOLD, BLUR_KERNEL, THRESH_VALUE, DILATE_ITERATIONS,
    MOTION_COOLDOWN_SECONDS, MOTION_CLIP_SECONDS, MOTION_IGNORE_ZONES,
    MIN_FREE_GB,
)


def cleanup_old_files(directory, min_free_gb=MIN_FREE_GB):
    """Delete oldest files in directory if free disk space is below min_free_gb"""
    free_gb = shutil.disk_usage('/').free / (1024**3)
    if free_gb < min_free_gb:
        files = [os.path.join(directory, f) for f in os.listdir(directory)]
        files.sort(key=os.path.getmtime)  # Oldest first
        while files and free_gb < min_free_gb:
            oldest = files.pop(0)
            try:
                os.remove(oldest)
                print(f"Deleted old file: {oldest}")
                free_gb = shutil.disk_usage('/').free / (1024**3)
            except OSError as e:
                print(f"Error deleting {oldest}: {e}")


class DoorCamera:
    def __init__(self):
        self.picam2 = None
        self.running = False
        self.save_dir = SAVE_DIR
        os.makedirs(self.save_dir, exist_ok=True)
        self.clips_dir = CLIPS_DIR
        os.makedirs(self.clips_dir, exist_ok=True)
        self.bg_subtractor = None
        self.thread = None
        self.last_capture = 0

    def start(self):
        if self.running:
            return
        self.running = True
        try:
            self.picam2 = Picamera2()
            frame_duration_us = int(1_000_000 / RECORDING_FPS)
            config = self.picam2.create_preview_configuration(
                main={"size": MAIN_RES, "format": "RGB888"}, lores={"size": LORES_RES},
                controls={"FrameDurationLimits": (frame_duration_us, frame_duration_us)},
            )
            self.picam2.configure(config)
            self.picam2.start()
            time.sleep(2)
            self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=THRESH_VALUE, detectShadows=True)
            # Warm up the background model so repetitive motion (e.g. a plant swaying)
            # is learned as background before the detection loop starts acting on it.
            for _ in range(50):
                warmup_yuv = self.picam2.capture_array("lores")
                warmup_gray = cv2.cvtColor(warmup_yuv, cv2.COLOR_YUV2GRAY_I420)
                warmup_gray = cv2.GaussianBlur(warmup_gray, (BLUR_KERNEL, BLUR_KERNEL), 0)
                self.bg_subtractor.apply(warmup_gray)
                time.sleep(0.1)
            print("Motion detection started.")
            self.thread = threading.Thread(target=self._detect_loop)
            self.thread.start()
        except RuntimeError as e:
            print(f"Failed to start camera: {e}")
            self.running = False

    def stop(self):
        self.running = False
        # Wait for the detect loop to fully exit (it may be mid-recording) before touching
        # picam2 here, since it also stops/restarts the camera after each capture event -
        # doing both from separate threads at once corrupts picamera2's internal state.
        if self.thread:
            self.thread.join()
        if self.picam2:
            self.picam2.stop()
            self.picam2.close()
        print("Motion detection stopped.")

    def _detect_loop(self):
        while self.running:
            frame_yuv = self.picam2.capture_array("lores")
            frame_gray = cv2.cvtColor(frame_yuv, cv2.COLOR_YUV2GRAY_I420)
            frame_gray = cv2.GaussianBlur(frame_gray, (BLUR_KERNEL, BLUR_KERNEL), 0)
            # Update the adaptive background model and get the foreground mask
            fgmask = self.bg_subtractor.apply(frame_gray)
            # Drop shadow pixels (value 127) that MOG2 flags separately from real foreground (255)
            fgmask = cv2.threshold(fgmask, 200, 255, cv2.THRESH_BINARY)[1]
            # Blank out configured ignore zones (e.g. wind-blown foliage) before looking for motion
            for x1, y1, x2, y2 in MOTION_IGNORE_ZONES:
                cv2.rectangle(fgmask, (x1, y1), (x2, y2), 0, -1)
            fgmask = cv2.dilate(fgmask, None, iterations=DILATE_ITERATIONS)
            contours, _ = cv2.findContours(fgmask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            largest = max(contours, key=cv2.contourArea, default=None)
            max_area = cv2.contourArea(largest) if largest is not None else 0
            motion_detected = max_area > CONTOUR_THRESHOLD
            if motion_detected and (time.time() - self.last_capture) >= MOTION_COOLDOWN_SECONDS:
                self.last_capture = time.time()
                self._capture_event()
            time.sleep(0.1)

    def _capture_event(self):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        photo_path = os.path.join(self.save_dir, f"motion_{timestamp}.jpg")
        cv2.imwrite(photo_path, self.picam2.capture_array("main"))
        print(f"Motion detected! Photo saved as {photo_path}")
        cleanup_old_files(self.save_dir)

        clip_path = os.path.join(self.clips_dir, f"motion_{timestamp}.mp4")
        encoder = H264Encoder(framerate=RECORDING_FPS)
        output = FfmpegOutput(clip_path)
        try:
            self.picam2.start_recording(encoder, output)
            time.sleep(MOTION_CLIP_SECONDS)
        finally:
            self.picam2.stop_recording()
            # stop_recording() alone leaves the capture pipeline stalled: capture_array()
            # calls after a recording hang indefinitely unless the camera is fully restarted.
            self.picam2.stop()
            self.picam2.start()
        print(f"Clip saved as {clip_path}")
        cleanup_old_files(self.clips_dir)

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


# Global instance
camera = DoorCamera()
