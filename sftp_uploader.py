import os
import socket
import paramiko
from settings import (
    SFTP_ENABLED, SFTP_HOST, SFTP_PORT, SFTP_USERNAME, SFTP_PASSWORD, SFTP_REMOTE_DIR,
)

CONNECT_TIMEOUT_SECONDS = 10


def upload_file(local_path, remote_subdir):
    """Push local_path to <SFTP_REMOTE_DIR>/<remote_subdir> on the configured SFTP server.
    No-op if SFTP_ENABLED is false. Never raises - network/auth failures are logged and
    swallowed so a bad or unreachable SFTP server can never affect motion detection."""
    if not SFTP_ENABLED:
        return

    transport = None
    sock = None
    try:
        # Connect the socket ourselves with a bounded timeout - Transport's own socket
        # setup has no timeout, so an unreachable host could otherwise hang for minutes.
        sock = socket.create_connection((SFTP_HOST, SFTP_PORT), timeout=CONNECT_TIMEOUT_SECONDS)
        transport = paramiko.Transport(sock)
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = transport.open_sftp_client()
        try:
            sftp.chdir(SFTP_REMOTE_DIR)
        except IOError:
            sftp.mkdir(SFTP_REMOTE_DIR)
            sftp.chdir(SFTP_REMOTE_DIR)
        try:
            sftp.chdir(remote_subdir)
        except IOError:
            sftp.mkdir(remote_subdir)
            sftp.chdir(remote_subdir)

        remote_path = os.path.basename(local_path)
        sftp.put(local_path, remote_path)
        print(f"Uploaded {local_path} to SFTP server at {SFTP_REMOTE_DIR}/{remote_subdir}/{remote_path}")
    except Exception as e:
        print(f"Warning: SFTP upload of {local_path} failed: {e}")
    finally:
        if transport is not None:
            transport.close()
        elif sock is not None:
            sock.close()
