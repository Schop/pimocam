import time
from motion_detection import detector, scheduler
from webserver import app
from settings import WEBSERVER_HOST, WEBSERVER_PORT, WEBSERVER_DEBUG

if __name__ == '__main__':
    # Start motion detection
    detector.start()
    try:
        # Run webserver
        app.run(host=WEBSERVER_HOST, port=WEBSERVER_PORT, debug=WEBSERVER_DEBUG)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        detector.stop()
        scheduler.shutdown()