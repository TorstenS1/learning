#!/bin/bash
# Azure App Service startup script for ALIS Backend

echo "Starting ALIS Backend..."

# Install dependencies if needed
if [ ! -d "/home/site/wwwroot/.venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv /home/site/wwwroot/.venv
fi

echo "Activating virtual environment..."
source /home/site/wwwroot/.venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r /home/site/wwwroot/requirements.txt

echo "Starting Gunicorn..."
cd /home/site/wwwroot
gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 2 backend.app:app
