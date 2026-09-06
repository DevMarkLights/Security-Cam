#!/usr/bin/env python3
import datetime
import os
import re

RECORDINGS_DIR = '/mnt/nvme/Security-Cam/backend'
RETENTION_DAYS = 10
_DATE_FILE = re.compile(r'^\d{4}-\d{2}-\d{2}\.mp4$')

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
    cleanup()