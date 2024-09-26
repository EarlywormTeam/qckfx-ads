#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Function to download a file only if it doesn't already exist
download_hf_if_not_exists() {
    local url=$1
    local dest_dir=$2
    local filename=$(basename "$url")
    if [ ! -f "$dest_dir/$filename" ]; then
        echo "Downloading $filename..."
        wget --header="Authorization: Bearer ${HF_TOKEN}" -P "$dest_dir" "$url"
    else
        echo "$filename already exists. Skipping download."
    fi
}

download_if_not_exists() {
    local url=$1
    local dest_dir=$2
    if [ ! -f "$dest_dir" ]; then
        echo "Downloading $dest_dir..."
        wget -O "$dest_dir" "$url"
    else
        echo "$dest_dir already exists. Skipping download."
    fi
}

# Function to install a node only if it's not already installed
install_node_if_not_exists() {
    local node=$1
    # Retrieve the list of installed nodes
    local installed_nodes
    installed_nodes=$(comfy node show installed)

    # Check if the node is in the list of installed nodes
    if echo "$installed_nodes" | grep -qw "$node"; then
        echo "Node '$node' is already installed. Skipping."
    else
        echo "Installing node '$node'..."
        comfy node install "$node"
    fi
}

# Function to install ComfyUI if not already installed
install_comfyui_if_not_exists() {
    local install_path="/app/ComfyUI"
    if [ -d "$install_path" ]; then
        echo "ComfyUI is already installed at $install_path. Skipping installation."
    else
        echo "Installing ComfyUI..."
        # Replace the following line with the actual ComfyUI installation command
        # For example:
        # git clone https://github.com/comfyanonymous/ComfyUI.git "$install_path"
        # or any other installation steps required
        comfy install --path "$install_path"  # Example placeholder
    fi
}

# Install ComfyUI if needed
install_comfyui_if_not_exists

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p /app/ComfyUI/models/unet
mkdir -p /app/ComfyUI/models/vae
mkdir -p /app/ComfyUI/models/clip
mkdir -p /app/ComfyUI/models/loras/xlabs/controlnets
mkdir -p /app/ComfyUI/models/loras/flux_realism
mkdir -p /app/ComfyUI/models/loras/med_intense_can
mkdir -p /app/ComfyUI/comfyui_filesystem
mkdir -p /app/ComfyUI/models/checkpoints/sdxl

# Download models
echo "Downloading models..."

# Unet model
download_hf_if_not_exists "https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/flux1-dev.safetensors" "/app/ComfyUI/models/unet"

download_if_not_exists "https://civitai.com/api/download/models/782002?type=Model&format=SafeTensor&size=full&fp=fp16" "/app/ComfyUI/models/checkpoints/sdxl/juggernautXL_v9Rdphoto2Lightning.safetensors"

download_hf_if_not_exists "https://huggingface.co/Justin-Choo/epiCRealism-Natural_Sin_RC1_VAE/resolve/main/epicrealism_naturalSinRC1VAE.safetensors" "/app/ComfyUI/models/checkpoints"

# VAE model
vae_model="/app/ComfyUI/models/vae/ae.safetensors"
if [ ! -f "$vae_model" ]; then
    echo "Downloading VAE model..."
    comfy --skip-prompt model download --url https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/ae.safetensors --relative-path /app/ComfyUI/models/vae
else
    echo "VAE model already exists. Skipping download."
fi

# Clip models
clip1="/app/ComfyUI/models/clip/clip_l.safetensors"
clip2="/app/ComfyUI/models/clip/t5xxl_fp16.safetensors"

if [ ! -f "$clip1" ]; then
    echo "Downloading Clip model clip_l.safetensors..."
    comfy --skip-prompt model download --url https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors --relative-path /app/ComfyUI/models/clip
else
    echo "Clip model clip_l.safetensors already exists. Skipping download."
fi

if [ ! -f "$clip2" ]; then
    echo "Downloading Clip model t5xxl_fp16.safetensors..."
    comfy --skip-prompt model download --url https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp16.safetensors --relative-path /app/ComfyUI/models/clip
else
    echo "Clip model t5xxl_fp16.safetensors already exists. Skipping download."
fi

# Med Intense Can Lora model
echo "Downloading Med Intense Can Lora model..."
lora_file="/app/ComfyUI/models/loras/med_intense_can.safetensors"
if [ ! -f "$lora_file" ]; then
    wget --header="Authorization: Bearer ${REPLICATE_API_TOKEN}" -P /app/ComfyUI/models/loras/med_intense_can https://replicate.delivery/yhqm/QRnYk8tBa84yCtjZC4ZfpJB4pHKL3vgZoVJwhOYqhpc6eEXTA/trained_model.tar
    tar -xvf "/app/ComfyUI/models/loras/med_intense_can/trained_model.tar" -C /app/ComfyUI/models/loras/med_intense_can
    mv /app/ComfyUI/models/loras/med_intense_can/output/flux_train_replicate/lora.safetensors /app/ComfyUI/models/loras/med_intense_can.safetensors
    rm -rf /app/ComfyUI/models/loras/med_intense_can/trained_model.tar /app/ComfyUI/models/loras/med_intense_can/output
else
    echo "Med Intense Can Lora model already exists. Skipping download."
fi

# Cognato cab model
echo "Downloading Cognato cab Lora model..."
lora_file="/app/ComfyUI/models/loras/cognato_cab.safetensors"
if [ ! -f "$lora_file" ]; then
    wget --header="Authorization: Bearer ${REPLICATE_API_TOKEN}" -P /app/ComfyUI/models/loras/cognato_cab https://replicate.delivery/yhqm/022tygSgjPrULhfDIxR1i0dgJnoafoav3Uhw3kshGyVhj2fmA/trained_model.tar 
    tar -xvf "/app/ComfyUI/models/loras/cognato_cab/trained_model.tar" -C /app/ComfyUI/models/loras/cognato_cab
    mv /app/ComfyUI/models/loras/cognato_cab/output/flux_train_replicate/lora.safetensors /app/ComfyUI/models/loras/cognato_cab.safetensors
    rm -rf /app/ComfyUI/models/loras/cognato_cab/trained_model.tar /app/ComfyUI/models/loras/cognato_cab/output
else
    echo "Cognato Lora model already exists. Skipping download."
fi

# anti-blur model
echo "Downloading anti-blur Lora model..."
lora_file="/app/ComfyUI/models/loras/FLUX-dev-lora-AntiBlur.safetensors"
if [ ! -f "$lora_file" ]; then
    comfy --skip-prompt model download --url https://huggingface.co/Shakker-Labs/FLUX.1-dev-LoRA-AntiBlur/resolve/main/FLUX-dev-lora-AntiBlur.safetensors --relative-path /app/ComfyUI/models/loras 
else
    echo "Anti-blur Lora model already exists. Skipping download."
fi

# Flux Canny ControlNet model
controlnet_model="/app/ComfyUI/models/xlabs/controlnets/flux-canny-controlnet_v2.safetensors"
if [ ! -f "$controlnet_model" ]; then
    echo "Downloading Flux Canny ControlNet model..."
    comfy --skip-prompt model download --url https://huggingface.co/XLabs-AI/flux-controlnet-collections/resolve/main/flux-canny-controlnet_v2.safetensors --relative-path /app/ComfyUI/models/xlabs/controlnets
else
    echo "Flux Canny ControlNet model already exists. Skipping download."
fi

# Copy ControlNet model
echo "Copying ControlNet model..."
if [ ! -f "/app/ComfyUI/models/controlnet/controlnet.safetensors" ]; then
    mkdir -p /app/ComfyUI/models/controlnet  # Ensure the destination directory exists
    cp "$controlnet_model" /app/ComfyUI/models/controlnet/controlnet.safetensors
    echo "ControlNet model copied successfully."
else
    echo "ControlNet model already copied. Skipping."
fi

# Flux Realism Lora model
flux_realism_model="/app/ComfyUI/models/loras/flux_realism/lora.safetensors"
if [ ! -f "$flux_realism_model" ]; then
    echo "Downloading Flux Realism Lora model..."
    download_hf_if_not_exists "https://huggingface.co/XLabs-AI/flux-RealismLora/resolve/main/lora.safetensors" "/app/ComfyUI/models/loras/flux_realism"
else
    echo "Flux Realism Lora model already exists. Skipping download."
fi

# Stability Canny Control Lora
canny_model="/app/ComfyUI/models/controlnet/sdxl/control-LoRAs-rank128"
if [ ! -f "$canny_model" ]; then
    echo "Downloading stability canny control lora model..."
    comfy --skip-prompt model download --url https://huggingface.co/stabilityai/control-lora/resolve/main/control-LoRAs-rank128/control-lora-canny-rank128.safetensors --relative-path /app/ComfyUI/models/controlnet/sdxl/control-LoRAs-rank128
else
    echo "Stability canny control lora model already exists. Skipping download."
fi

# Install custom nodes
echo "Installing custom nodes..."
custom_nodes=(
    "comfyui_segment_anything"
    "x-flux-comfyui"
    "Jovimetrix"
    "ComfyUI_Comfyroll_CustomNodes"
    "rgthree-comfy"
    "comfyui_controlnet_aux"
    "ComfyUI_essentials"
    "ComfyUI-Impact-Pack"
    "Derfuu_ComfyUI_ModdedNodes"
    "comfyui-various"
    "ComfyUI-Image-Filters"
    "ComfyUI-KJNodes"
    "comfyui-mixlab-nodes"
    "ComfyUI_Noise"
    "comfyui-tensorops"
    "masquerade-nodes-comfyui"
    "https://github.com/EarlywormTeam/was-node-suite-comfyui.git"
    "ComfyUI_LayerStyle"
    "ComfyUI-IC-Light"
    "CharacterFaceSwap"
    "mikey_nodes"
)

for node in "${custom_nodes[@]}"; do
    install_node_if_not_exists "$node"
done

echo "ComfyUI setup completed successfully."

