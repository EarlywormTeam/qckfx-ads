FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN mkdir -p /app/ComfyUI
VOLUME /app/ComfyUI

RUN pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu124

# Copy the necessary files from the host 
COPY requirements.txt . 

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY workflows/ /app/workflows/
COPY main.py . 
COPY startup.sh .

# Expose necessary ports
EXPOSE 8000
EXPOSE 8188

RUN chmod +x startup.sh

# Command to run the FastAPI application
ENTRYPOINT ["/app/startup.sh"]
