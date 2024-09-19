# ================================
# Stage 1: Base Image with Comfy 
# ================================
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install comfy-cli and other Python dependencies
RUN pip install --upgrade pip
RUN pip install git+https://github.com/florisvanderharst/comfy-cli.git@fix-background-run python-dotenv

# Clone ComfyUI repository
RUN git clone https://github.com/comfyanonymous/ComfyUI.git

# Set working directory to ComfyUI
WORKDIR /app/ComfyUI

# Install ComfyUI dependencies
RUN comfy --skip-prompt install --nvidia

# ================================
# Stage 1: Install Models
# ================================
FROM base AS models 

WORKDIR /app/ComfyUI

# Download models
# It's essential to use build arguments or environment variables for tokens
ARG HF_TOKEN
ARG REPLICATE_API_TOKEN

# Create directories for models
RUN mkdir -p models/unet models/vae models/clip models/loras/xlabs/controlnets models/loras/flux_realism models/loras/med_intense_can

# Download models
RUN wget --header="Authorization: Bearer ${HF_TOKEN}" -P models/unet https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/flux1-dev.safetensors

RUN comfy --skip-prompt model download --url https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/ae.safetensors --relative-path models/vae

RUN comfy --skip-prompt model download --url https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors --relative-path models/clip

RUN comfy --skip-prompt model download --url https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp16.safetensors --relative-path models/clip

RUN wget --header="Authorization: Bearer ${REPLICATE_API_TOKEN}" -P /models/loras/med_intense_can https://replicate.delivery/yhqm/QRnYk8tBa84yCtjZC4ZfpJB4pHKL3vgZoVJwhOYqhpc6eEXTA/trained_model.tar && \
    tar -xvf /models/loras/med_intense_can/trained_model.tar -C /models/loras/med_intense_can && \
    mv /models/loras/med_intense_can/output/flux_train_replicate/lora.safetensors models/loras/med_intense_can.safetensors && \
    rm -rf /models

RUN comfy --skip-prompt model download --url https://huggingface.co/XLabs-AI/flux-controlnet-collections/resolve/main/flux-canny-controlnet_v2.safetensors --relative-path models/xlabs/controlnets

RUN cp models/xlabs/controlnets/flux-canny-controlnet_v2.safetensors models/controlnet/controlnet.safetensors

RUN wget --header="Authorization: Bearer ${HF_TOKEN}" -P models/loras/flux_realism https://huggingface.co/XLabs-AI/flux-RealismLora/resolve/main/lora.safetensors

# ================================
# Stage 3: Install Custom Nodes 
# ================================
FROM models AS nodes

WORKDIR /app/ComfyUI

# Install custom nodes
RUN comfy node install comfyui_segment_anything
RUN comfy node install x-flux-comfyui
RUN comfy node install Jovimetrix
RUN comfy node install ComfyUI_Comfyroll_CustomNodes
RUN comfy node install rgthree-comfy
RUN comfy node install comfyui_controlnet_aux
RUN comfy node install ComfyUI_essentials
RUN comfy node install ComfyUI-Impact-Pack
RUN comfy node install Derfuu_ComfyUI_ModdedNodes
RUN comfy node install comfyui-various
RUN comfy node install ComfyUI-Image-Filters
RUN comfy node install ComfyUI-KJNodes
RUN comfy node install comfyui-mixlab-nodes
RUN comfy node install ComfyUI_Noise
RUN comfy node install comfyui-tensorops
RUN comfy node install masquerade-nodes-comfyui
RUN comfy node install https://github.com/EarlywormTeam/was-node-suite-comfyui.git

# ================================
# Stage 4: Application Layer 
# ================================ 
FROM nodes AS app

# Copy the necessary files from the base stage
COPY --from=base /app/ComfyUI /app/ComfyUI
COPY workflows/ /app/workflows/
COPY custom_nodes/ /app/ComfyUI/custom_nodes/
COPY main.py /app/
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose necessary ports
EXPOSE 8000

# Command to run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

