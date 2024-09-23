#!/bin/bash
set -e

# Check if ComfyUI requirements file exists
if [ -f /app/ComfyUI/requirements.txt ]; then
    echo "Installing ComfyUI dependencies..."
    pip install -r /app/ComfyUI/requirements.txt
else
    echo "ComfyUI requirements.txt not found. Skipping."
fi

pip install -r /app/ComfyUI/custom_nodes/was-node-suite-comfyui/requirements.txt

git config --global --add safe.directory /app/ComfyUI

comfy --skip-prompt --workspace=/app/ComfyUI node fix all

# Run the main application
uvicorn main:app --host 0.0.0.0 --port 8000
