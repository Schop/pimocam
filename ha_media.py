import os
import shutil
from settings import HA_MEDIA_DIR


def publish_to_ha(local_path, subdir):
    """Copy local_path into <HA_MEDIA_DIR>/<subdir> so it shows up in Home Assistant's
    Media Browser. No-op if HA_MEDIA_DIR isn't set. Never raises - if the network share
    isn't mounted, this must not affect motion detection."""
    if not HA_MEDIA_DIR:
        return
    try:
        dest_dir = os.path.join(HA_MEDIA_DIR, subdir)
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copy2(local_path, os.path.join(dest_dir, os.path.basename(local_path)))
        print(f"Published {local_path} to Home Assistant media at {dest_dir}")
    except OSError as e:
        print(f"Warning: publish to Home Assistant media failed: {e}")
