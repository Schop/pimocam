import time
from motion_detection import detector, scheduler, sync_to_gdrive
from webserver import app
from settings import WEBSERVER_HOST
from db_settings import get_setting

if __name__ == '__main__':
    # Start motion detection
    detector.start()
    scheduler_interval = get_setting('SCHEDULER_INTERVAL_MINUTES', 30)
    scheduler.add_job(func=lambda: detector.capture_timelapse(), trigger="interval", minutes=scheduler_interval)
    scheduler.add_job(func=sync_to_gdrive, trigger="interval", hours=1)
    scheduler.start()
    try:
        # Run webserver
        port = get_setting('WEBSERVER_PORT', 5000)
        debug = get_setting('WEBSERVER_DEBUG', True)
        app.run(host=WEBSERVER_HOST, port=port, debug=debug)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        detector.stop()
        scheduler.shutdown()