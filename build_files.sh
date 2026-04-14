#!/bin/bash
set -e
echo "BUILD START"

# Build the React frontend
echo "Building React frontend..."
cd frontend
npm install
npm run build
cd ..

# Build Django backend
echo "Building Django backend..."
python3 -m pip install -r requirements.txt --break-system-packages
python3 BanglaCERT/manage.py migrate --noinput
python3 BanglaCERT/manage.py collectstatic --noinput --clear
echo "BUILD END"
