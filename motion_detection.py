import cv2
import numpy as np
from picamera2 import Picamera2
import time
import os

def main():
    # Initialize the camera
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (2304, 1296), "format": "RGB888"}, lores={"size": (640, 480)})
    picam2.configure(config)
    picam2.start()

    # Allow camera to warm up
    time.sleep(2)

    save_dir = "/home/schop/Pictures"
    os.makedirs(save_dir, exist_ok=True)

    # Capture first frame for comparison
    frame1_yuv = picam2.capture_array("lores")
    frame1_color = cv2.cvtColor(frame1_yuv, cv2.COLOR_YUV2RGB_I420)
    frame1 = cv2.cvtColor(frame1_color, cv2.COLOR_BGR2GRAY)
    frame1 = cv2.GaussianBlur(frame1, (31, 31), 0)

    print("Motion detection started. Press Ctrl+C to stop.")

    try:
        while True:
            # Capture current frame
            frame2_yuv = picam2.capture_array("lores")
            frame2_color = cv2.cvtColor(frame2_yuv, cv2.COLOR_YUV2RGB_I420)
            frame2 = cv2.cvtColor(frame2_color, cv2.COLOR_BGR2GRAY)
            frame2 = cv2.GaussianBlur(frame2, (31, 31), 0)

            # Compute the absolute difference between the current frame and the previous frame
            frame_diff = cv2.absdiff(frame1, frame2)
            thresh = cv2.threshold(frame_diff, 50, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)

            # Find contours in the thresholded image
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            motion_detected = False
            for contour in contours:
                if cv2.contourArea(contour) < 1000:  # Adjust this value based on your needs
                    continue
                motion_detected = True
                break

            if motion_detected:
                # Generate timestamp for filename
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = os.path.join(save_dir, f"motion_{timestamp}.jpg")
                # Save the high-res color image
                cv2.imwrite(filename, picam2.capture_array("main"))
                print(f"Motion detected! Image saved as {filename}")
                # Wait for 5 seconds to avoid multiple captures for the same motion
                time.sleep(5)

            # Update the previous frame
            frame1 = frame2

            # Small delay to reduce CPU usage
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Stopping motion detection.")
    finally:
        picam2.stop()

if __name__ == "__main__":
    main()