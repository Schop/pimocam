# Raspberry Pi Door Camera

A Python-based motion-triggered camera for a Raspberry Pi, watching a front door/driveway. Saves a photo and a short video clip on each motion event, with a web interface for browsing captures.

## Features
- Motion-triggered photo + video clip capture (OpenCV MOG2 background subtraction)
- Configurable ignore zones to exclude parts of the frame (e.g. a plant moving in the wind)
- Web interface for browsing photos and clips
- Configurable save directories via environment variables

## Setup
1. Clone the repository: `git clone https://github.com/Schop/pimocam.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Install ffmpeg (used to encode video clips): `sudo apt install ffmpeg`
4. Run: `python webserver.py`

## Configuration
- Edit `settings.py` to customize save directories, camera resolutions, and motion detection tuning (sensitivity, minimum motion size, cooldown, clip length, ignore zones).
- Set `SAVE_DIR`/`CLIPS_DIR` environment variables to override the default save locations.
- Optional remote backup: set `SFTP_ENABLED=true` plus `SFTP_HOST`, `SFTP_PORT`, `SFTP_USERNAME`, `SFTP_PASSWORD`, and `SFTP_REMOTE_DIR` as environment variables to push every captured photo/clip to a remote SFTP server (files also stay on local disk). Never put these values directly in `settings.py`. If you're using the remote gallery below, `SFTP_REMOTE_DIR` must point at the external data directory (**outside** the gallery's document root), not the docroot itself.

## Web Interface
- Access at `http://your_pi_ip:5000`
- Browse recent photos (`/`) and clips (`/clips`)
- Start/stop motion detection (`/start`, `/stop`)

## Remote gallery (server room)
If SFTP backup is enabled (see Configuration), `remote_gallery/` is a small PHP site to browse the uploaded copies from a subdomain on the server-room machine, gated behind an app-level login (not `.htaccess`, since that's Apache-only and won't work on nginx or on shared hosting without server-config access). The actual photos/clips are kept **outside** the web document root, so there's no URL that can reach them except through the authenticated pages.

1. Copy the contents of `remote_gallery/` (all the `.php` files) to the subdomain's document root.
2. Create a data directory **outside** the document root, e.g. a sibling of it like `/home/youruser/pimocam_data/` — this holds the `photos/`/`clips/` subfolders. Set `SFTP_REMOTE_DIR` (Pi-side environment variable) to this path, not the docroot.
3. Copy `config.example.php` to a path **outside** the document root too (e.g. `/home/youruser/pimocam_config.php`) and rename it `config.php`. Fill in `data_dir` (the path from step 2) and `username`.
4. Temporarily upload `hash_password.php` into the docroot, visit it in a browser, enter your chosen password, and paste the resulting hash into `config.php`'s `password_hash`. **Delete `hash_password.php` from the server** once you've done this — it must not be left reachable.
5. Edit `remote_gallery/config_path.php` (in the docroot) and set the returned string to the absolute path of `config.php` from step 3. This is the one place both `login.php` and `auth.php` read to find your config.
6. Visit `index.php` on the subdomain — it should redirect to `login.php`. Log in with the username/password from step 3/4.

Photos/clips are served through `media.php`, which checks the session before streaming anything and validates the requested filename, so the media stays inaccessible without logging in first — no `.htaccess` or web server configuration required.

## Files
- `webserver.py`: Entry point and Flask web interface
- `camera.py`: Camera lifecycle and motion detection/capture logic
- `settings.py`: Configuration settings
- `sftp_uploader.py`: Optional SFTP backup of captures to a remote server
- `remote_gallery/`: Optional PHP gallery for browsing the SFTP-uploaded copies remotely
- `requirements.txt`: Dependencies
