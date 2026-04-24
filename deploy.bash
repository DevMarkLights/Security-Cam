#!/bin/bash
cd /mnt/nvme/Security-Cam

git pull

cd frontend
npm run build

cd ../backend
.venv/bin/pip install -r requirements.txt --quiet

rm -rf dist

cd ../frontend
cp -r dist ../backend

sudo systemctl restart security.service
