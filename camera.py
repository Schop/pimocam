import cv2
import time
import os
import json
import threading
import shutil
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput
from sftp_uploader import upload_file
from settings import (
    SAVE_DIR, CLIPS_DIR, MAIN_RES, LORES_RES, RECORDING_FPS,
    CONTOUR_THRESHOLD, BLUR_KERNEL, THRESH_VALUE, DILATE_ITERATIONS,
    MOTION_COOLDOWN_SECONDS, MOTION_CLIP_SECONDS, MOTION_IGNORE_ZONES,
    MIN_FREE_GB,
)

RUNTIME_SETTINGS_PATH = os.path.join(os.path.dirname(__file__), 'runtime_settings.json')


def _load_runtime_overrides():
    """Read runtime_settings.json if present; return {} on missing/corrupt file."""
    if not os.path.exists(RUNTIME_SETTINGS_PATH):
        return {}
    try:
        with open(RUNTIME_SETTINGS_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: could not read {RUNTIME_SETTINGS_PATH}: {e}; using settings.py defaults")
        return {}


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

        overrides = _load_runtime_overrides()
        self.contour_threshold = overrides.get('contour_threshold', CONTOUR_THRESHOLD)
        self.thresh_value = overrides.get('thresh_value', THRESH_VALUE)
        self.dilate_iterations = overrides.get('dilate_iterations', DILATE_ITERATIONS)

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
            self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=self.thresh_value, detectShadows=True)
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
            # Pull lores + main from a single request so they're the exact same instant -
            # two separate capture_array() calls would let the object keep moving between
            # the frame that trips detection and the frame actually saved as the photo.
            request = self.picam2.capture_request()
            try:
                frame_yuv = request.make_array("lores")
                frame_gray = cv2.cvtColor(frame_yuv, cv2.COLOR_YUV2GRAY_I420)
                frame_gray = cv2.GaussianBlur(frame_gray, (BLUR_KERNEL, BLUR_KERNEL), 0)
                # Update the adaptive background model and get the foreground mask
                fgmask = self.bg_subtractor.apply(frame_gray)
                # Drop shadow pixels (value 127) that MOG2 flags separately from real foreground (255)
                fgmask = cv2.threshold(fgmask, 200, 255, cv2.THRESH_BINARY)[1]
                # Blank out configured ignore zones (e.g. wind-blown foliage) before looking for motion
                for x1, y1, x2, y2 in MOTION_IGNORE_ZONES:
                    cv2.rectangle(fgmask, (x1, y1), (x2, y2), 0, -1)
                fgmask = cv2.dilate(fgmask, None, iterations=self.dilate_iterations)
                contours, _ = cv2.findContours(fgmask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                largest = max(contours, key=cv2.contourArea, default=None)
                max_area = cv2.contourArea(largest) if largest is not None else 0
                motion_detected = max_area > self.contour_threshold
                if motion_detected and (time.time() - self.last_capture) >= MOTION_COOLDOWN_SECONDS:
                    self.last_capture = time.time()
                    # Bounding box of the triggering blob, in lores (640x480) coordinates -
                    # same coordinate space as MOTION_IGNORE_ZONES.
                    bbox = cv2.boundingRect(largest)
                    frame = request.make_array("main")
                    self._capture_event(max_area, bbox, frame)
            finally:
                request.release()
            time.sleep(0.1)

    def _capture_event(self, contour_area, bbox, frame):
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        photo_path = os.path.join(self.save_dir, f"motion_{timestamp}.jpg")

        # Draw the triggering blob's bounding box on the saved photo, scaled up from the
        # lores detection frame to the main frame, so it's obvious what caused the capture.
        x, y, w, h = bbox
        scale_x = MAIN_RES[0] / LORES_RES[0]
        scale_y = MAIN_RES[1] / LORES_RES[1]
        top_left = (int(x * scale_x), int(y * scale_y))
        bottom_right = (int((x + w) * scale_x), int((y + h) * scale_y))
        cv2.rectangle(frame, top_left, bottom_right, (0, 0, 255), 3)

        cv2.imwrite(photo_path, frame)
        print(f"Motion detected! Photo saved as {photo_path}")
        print(f"  Trigger values: contour_area={contour_area:.0f}, contour_threshold={self.contour_threshold}, "
              f"thresh_value={self.thresh_value}, bbox(lores)={bbox}")
        threading.Thread(target=upload_file, args=(photo_path, 'photos'), daemon=True).start()

        # Sidecar file recording the values that triggered this capture, so the web UI
        # can show them next to the photo to help tune sensitivity settings.
        metadata_path = os.path.splitext(photo_path)[0] + '.json'
        with open(metadata_path, 'w') as f:
            json.dump({
                'contour_area': contour_area,
                'contour_threshold': self.contour_threshold,
                'thresh_value': self.thresh_value,
                'bbox': bbox,
            }, f)
        threading.Thread(target=upload_file, args=(metadata_path, 'photos'), daemon=True).start()

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
        threading.Thread(target=upload_file, args=(clip_path, 'clips'), daemon=True).start()
        cleanup_old_files(self.clips_dir)

    def capture_image(self):
        # self.picam2 stays a closed instance after stop() rather than becoming None,
        # so it isn't enough on its own to tell whether the camera can actually capture.
        if not self.running or not self.picam2:
            print("Camera not running")
            return None
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.save_dir, f"capture_{timestamp}.jpg")
        self.picam2.capture_file(filename)
        print(f"Image captured: {filename}")
        threading.Thread(target=upload_file, args=(filename, 'photos'), daemon=True).start()
        cleanup_old_files(self.save_dir)
        return filename

    def update_settings(self, contour_threshold=None, thresh_value=None, dilate_iterations=None):
        """Validate and apply new motion-sensitivity settings live, then persist them.
        Raises ValueError on invalid input; nothing is applied or persisted in that case."""
        new_contour = self.contour_threshold if contour_threshold is None else contour_threshold
        new_thresh = self.thresh_value if thresh_value is None else thresh_value
        new_dilate = self.dilate_iterations if dilate_iterations is None else dilate_iterations

        if not isinstance(new_contour, int) or not (1 <= new_contour <= 100000):
            raise ValueError("Contour threshold must be an integer between 1 and 100000.")
        if not isinstance(new_thresh, (int, float)) or not (1 <= new_thresh <= 200):
            raise ValueError("Sensitivity threshold must be a number between 1 and 200.")
        if not isinstance(new_dilate, int) or not (0 <= new_dilate <= 10):
            raise ValueError("Dilate iterations must be an integer between 0 and 10.")

        self.contour_threshold = new_contour
        self.thresh_value = new_thresh
        self.dilate_iterations = new_dilate

        if self.bg_subtractor is not None:
            self.bg_subtractor.setVarThreshold(self.thresh_value)

        self._save_runtime_overrides()

    def _save_runtime_overrides(self):
        data = {
            'contour_threshold': self.contour_threshold,
            'thresh_value': self.thresh_value,
            'dilate_iterations': self.dilate_iterations,
        }
        tmp_path = RUNTIME_SETTINGS_PATH + '.tmp'
        with open(tmp_path, 'w') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, RUNTIME_SETTINGS_PATH)


# Global instance
camera = DoorCamera()
