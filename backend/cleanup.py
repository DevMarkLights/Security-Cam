#!/usr/bin/env python3
import datetime
import os
import re
import struct
import subprocess

RECORDINGS_DIR = '/mnt/nvme/Security-Cam/backend'
RETENTION_DAYS = 10
_DATE_FILE = re.compile(r'^\d{4}-\d{2}-\d{2}\.mp4$')

def _moov_at_end(path):
    """Returns True if the moov atom comes after mdat (needs faststart re-encode)."""
    moov_pos = None
    mdat_pos = None
    try:
        with open(path, 'rb') as f:
            while True:
                header = f.read(8)
                if len(header) < 8:
                    break
                size = struct.unpack('>I', header[:4])[0]
                atom_type = header[4:8].decode('ascii', errors='ignore')
                if atom_type == 'moov':
                    moov_pos = f.tell() - 8
                elif atom_type == 'mdat':
                    mdat_pos = f.tell() - 8
                if size == 0:
                    break
                elif size == 1:
                    ext = f.read(8)
                    if len(ext) < 8:
                        break
                    size = struct.unpack('>Q', ext)[0]
                    f.seek(size - 16, 1)
                else:
                    f.seek(size - 8, 1)
    except Exception as e:
        print(f'Error reading {path}: {e}')
        return False

    if moov_pos is None or mdat_pos is None:
        return False
    return mdat_pos < moov_pos


def remux_existing():
    today = datetime.date.today().strftime('%Y-%m-%d') + '.mp4'
    for filename in os.listdir(RECORDINGS_DIR):
        if not _DATE_FILE.match(filename):
            continue
        if filename == today:
            print(f'Skipping {filename} (currently recording)')
            continue
        path = os.path.join(RECORDINGS_DIR, filename)
        if not _moov_at_end(path):
            print(f'OK: {filename}')
            continue
        print(f'Re-encoding: {filename}')
        tmp = path.replace('.mp4', '_tmp.mp4')
        result = subprocess.run(
            ['ffmpeg', '-y', '-i', path,
             '-c', 'copy',
             '-movflags', '+faststart', tmp],
            capture_output=True
        )
        if result.returncode == 0:
            os.replace(tmp, path)
            print(f'Done: {filename}')
        else:
            print(f'ffmpeg failed for {filename}: {result.stderr.decode()}')
            if os.path.exists(tmp):
                os.remove(tmp)


def cleanup():
    cutoff = datetime.date.today() - datetime.timedelta(days=RETENTION_DAYS)
    for filename in os.listdir(RECORDINGS_DIR):
        if not _DATE_FILE.match(filename):
            continue
        try:
            file_date = datetime.date.fromisoformat(filename[:-4])
        except ValueError:
            continue
        if file_date < cutoff:
            os.remove(os.path.join(RECORDINGS_DIR, filename))
            print(f'Deleted: {filename}')


if __name__ == '__main__':
    remux_existing()
    cleanup()