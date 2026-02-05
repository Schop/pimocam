import time
from motion_detection import detector, scheduler
from webserver import app

if __name__ == '__main__':
    # Start motion detection
    detector.start()
    try:
        # Run webserver
        app.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        detector.stop()
        scheduler.shutdown()