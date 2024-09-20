#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check if required environment variables are set
if [ -z "$HF_TOKEN" ] || [ -z "$REPLICATE_API_TOKEN" ]; then
    echo "Error: HF_TOKEN and REPLICATE_API_TOKEN must be set as environment variables."
    exit 1
fi

cd /mnt

# Install ComfyUI CLI and setup
echo "Installing ComfyUI dependencies..."
comfy --here --skip-prompt install --nvidia


# Create necessary directories
mkdir -p /mnt/ComfyUI/models/unet
mkdir -p /mnt/ComfyUI/models/vae
mkdir -p /mnt/ComfyUI/models/clip
mkdir -p /mnt/ComfyUI/models/loras/xlabs/controlnets
mkdir -p /mnt/ComfyUI/models/loras/flux_realism
mkdir -p /mnt/ComfyUI/models/loras/med_intense_can
mkdir -p /mnt/ComfyUI/comfyui_filesystem

# Download models
echo "Downloading Unet model..."
wget --header="Authorization: Bearer ${HF_TOKEN}" -P /mnt/ComfyUI/models/unet https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/flux1-dev.safetensors

echo "Downloading VAE model..."
comfy --skip-prompt model download --url https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/ae.safetensors --relative-path /mnt/ComfyUI/models/vae

echo "Downloading Clip models..."
comfy --skip-prompt model download --url https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors --relative-path /mnt/ComfyUI/models/clip
comfy --skip-prompt model download --url https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp16.safetensors --relative-path /mnt/ComfyUI/models/clip

echo "Downloading Med Intense Can Lora model..."
wget --header="Authorization: Bearer ${REPLICATE_API_TOKEN}" -P /mnt/ComfyUI/models/loras/med_intense_can https://replicate.delivery/yhqm/QRnYk8tBa84yCtjZC4ZfpJB4pHKL3vgZoVJwhOYqhpc6eEXTA/trained_model.tar && \
    tar -xvf /mnt/ComfyUI/models/loras/med_intense_can/trained_model.tar -C /mnt/ComfyUI/models/loras/med_intense_can && \
    mv /mnt/ComfyUI/models/loras/med_intense_can/output/flux_train_replicate/lora.safetensors /mnt/ComfyUI/models/loras/med_intense_can.safetensors && \
    rm -rf /mnt/ComfyUI/models/loras/med_intense_can/trained_model.tar

echo "Downloading Flux Canny ControlNet model..."
comfy --skip-prompt model download --url https://huggingface.co/XLabs-AI/flux-controlnet-collections/resolve/main/flux-canny-controlnet_v2.safetensors --relative-path /mnt/ComfyUI/models/xlabs/controlnets

echo "Copying ControlNet model..."
cp /mnt/ComfyUI/models/xlabs/controlnets/flux-canny-controlnet_v2.safetensors /mnt/ComfyUI/models/controlnet/controlnet.safetensors

echo "Downloading Flux Realism Lora model..."
wget --header="Authorization: Bearer ${HF_TOKEN}" -P /mnt/ComfyUI/models/loras/flux_realism https://huggingface.co/XLabs-AI/flux-RealismLora/resolve/main/lora.safetensors

# Install custom nodes (if needed)
echo "Installing custom nodes..."
comfy node install comfyui_segment_anything
comfy node install x-flux-comfyui
comfy node install Jovimetrix
comfy node install ComfyUI_Comfyroll_CustomNodes
comfy node install rgthree-comfy
comfy node install comfyui_controlnet_aux
comfy node install ComfyUI_essentials
comfy node install ComfyUI-Impact-Pack
comfy node install Derfuu_ComfyUI_ModdedNodes
comfy node install comfyui-various
comfy node install ComfyUI-Image-Filters
comfy node install ComfyUI-KJNodes
comfy node install comfyui-mixlab-nodes
comfy node install ComfyUI_Noise
comfy node install comfyui-tensorops

echo "ComfyUI setup completed successfully."

