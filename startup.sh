#!/bin/bash
# Azure App Service startup script for ALIS Backend

echo "Starting ALIS Backend..."
cd /home/site/wwwroot

# Check if we're in the right directory
echo "Current directory: $(pwd)"
echo "Files in directory:"
ls -la

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "ERROR: requirements.txt not found!"
    exit 1
fi

echo "Starting Gunicorn..."
# Use app:app since backend.app:app requires backend to be a package
gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 2 --chdir /home/site/wwwroot backend.app:app
