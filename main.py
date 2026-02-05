import time
from motion_detection import detector, scheduler, sync_to_gdrive
from webserver import app
from settings import WEBSERVER_HOST, WEBSERVER_PORT, WEBSERVER_DEBUG, SCHEDULER_INTERVAL_MINUTES

if __name__ == '__main__':
    # Start motion detection
    detector.start()
    scheduler.add_job(func=lambda: detector.capture_timelapse(), trigger="interval", minutes=SCHEDULER_INTERVAL_MINUTES)
    scheduler.add_job(func=sync_to_gdrive, trigger="interval", hours=1)
    scheduler.start()
    try:
        # Run webserver
        app.run(host=WEBSERVER_HOST, port=WEBSERVER_PORT, debug=WEBSERVER_DEBUG)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        detector.stop()
        scheduler.shutdown()