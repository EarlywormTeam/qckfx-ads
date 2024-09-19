# main.py
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import base64
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="ComfyUI API")

# Paths
BASE_DIR = Path(__file__).parent
COMFYUI_DIR = BASE_DIR / "ComfyUI"
WORKFLOWS_DIR = BASE_DIR / "workflows"
INPUT_DIR = COMFYUI_DIR / "input"
OUTPUT_DIR = COMFYUI_DIR / "output"

# Ensure directories exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Pydantic Models for Request Bodies
class FirstGenRequest(BaseModel):
    gen_id: str
    seed: int
    trigger_word: str
    prompt: str
    lora_name: str
    product_description: str
    detection_prompt: str
    count: int = 1  # Optional, default to 1

class RefineFirstGenRequest(BaseModel):
    gen_id: str
    seed: int
    prompt: str
    image: str  # Base64 encoded image

class RefineObjectRequest(BaseModel):
    gen_id: str
    original_prompt: str
    prompt: str
    image: str  # Base64 encoded image
    # seed: int  # Uncomment if needed

# Helper Functions
def run_comfy_command(cmd: str, cwd: Path = COMFYUI_DIR) -> None:
    """Run a ComfyUI command."""
    process = subprocess.run(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode != 0:
        print(f"Command failed: {cmd}")
        print(process.stdout.decode())
        print(process.stderr.decode())
        raise RuntimeError(f"Command failed: {cmd}")

def find_output_images(file_prefix: str) -> List[bytes]:
    """Find and return image bytes from the output directory based on the file prefix."""
    image_bytes_list = []
    for f in OUTPUT_DIR.iterdir():
        if f.is_file() and f.name.startswith(file_prefix):
            image_bytes_list.append(f.read_bytes())
    return image_bytes_list

def launch_comfyui():
    """Launch ComfyUI as a subprocess."""
    cmd = "comfy launch -- --listen 0.0.0.0 --port 8000"
    subprocess.Popen(cmd, shell=True, cwd=COMFYUI_DIR)
    print("ComfyUI launched.")

# Event Handlers
@app.on_event("startup")
def startup_event():
    """Launch ComfyUI when the FastAPI app starts."""
    # Check if ComfyUI is already running
    try:
        subprocess.run("curl --silent http://localhost:8000", shell=True, check=True)
        print("ComfyUI is already running.")
    except subprocess.CalledProcessError:
        print("Launching ComfyUI...")
        launch_comfyui()

# API Endpoints
@app.post("/first_gen")
def first_gen(request: FirstGenRequest):
    try:
        # Load the workflow template
        workflow_path = WORKFLOWS_DIR / "first_gen_workflow_api.json"
        workflow_data = json.loads(workflow_path.read_text())

        # Modify the workflow based on the request
        workflow_data["295"]["inputs"]["text"] = f"{request.trigger_word} {request.prompt}"
        workflow_data["185"]["inputs"]["text"] = f"{request.prompt}\nSharp, focused details, correct hands, fingers, and finger nails."
        workflow_data["231"]["inputs"]["text"] = f"{request.prompt}\nCrisp text, correct fingers and finger nails, in focus, sharp. Remove artifacts. Non-frizzy hair."

        # Set the number of images to generate
        workflow_data["304"]["inputs"]["batch_size"] = request.count

        # Set the filename prefix
        workflow_data["164"]["inputs"]["filename_prefix"] = f"{request.gen_id}_{request.seed}_first_gen"

        # Set the lora
        workflow_data["125"]["inputs"]["lora_name"] = request.lora_name

        # Set the product description
        workflow_data["6"]["inputs"]["text"] = request.product_description

        # Set the detection prompt
        detection_nodes = ["120", "128", "225", "243", "266", "283"]
        for node_id in detection_nodes:
            workflow_data[node_id]["inputs"]["prompt"] = request.detection_prompt

        # Set the seed
        seed_nodes = ["25", "192", "208", "211", "212", "236", "303"]
        for node_id in seed_nodes:
            workflow_data[node_id]["inputs"]["noise_seed"] = request.seed

        # Save the modified workflow
        new_workflow_file = WORKFLOWS_DIR / f"{request.gen_id}_{request.seed}_first_gen.json"
        with new_workflow_file.open("w") as f:
            json.dump(workflow_data, f)

        # Run the workflow
        run_comfy_command(f"comfy run --workflow {new_workflow_file} --wait --verbose --timeout 1200")

        # Retrieve output images
        image_bytes_list = find_output_images(f"{request.gen_id}_{request.seed}_first_gen")

        if not image_bytes_list:
            raise HTTPException(status_code=404, detail="No images found.")

        # Encode images as base64
        encoded_images = [base64.b64encode(img).decode('utf-8') for img in image_bytes_list]

        return JSONResponse(content={"images": encoded_images})

    except Exception as e:
        print(f"Error in first_gen: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/refine_first_gen")
def refine_first_gen(request: RefineFirstGenRequest):
    try:
        # Load the workflow template
        workflow_path = WORKFLOWS_DIR / "refined_first_gen_workflow_api.json"
        workflow_data = json.loads(workflow_path.read_text())

        # Decode and save the input image
        image_data = base64.b64decode(request.image)
        temp_file_name = f"{request.gen_id}_temp_input.png"
        temp_file_path = INPUT_DIR / temp_file_name

        with temp_file_path.open("wb") as f:
            f.write(image_data)

        # Use the temporary file as input
        workflow_data["47"]["inputs"]["image"] = temp_file_name

        # Insert the prompt
        workflow_data["6"]["inputs"]["text"] = request.prompt

        # Set the filename prefix
        workflow_data["165"]["inputs"]["filename_prefix"] = f"{request.gen_id}_refine_first_gen"

        # Save the modified workflow
        new_workflow_file = WORKFLOWS_DIR / f"{request.gen_id}_refine_first_gen.json"
        with new_workflow_file.open("w") as f:
            json.dump(workflow_data, f)

        # Run the workflow
        run_comfy_command(f"comfy run --workflow {new_workflow_file} --wait --verbose --timeout 1200")

        # Retrieve output images
        image_bytes_list = find_output_images(f"{request.gen_id}_refine_first_gen")

        if not image_bytes_list:
            raise HTTPException(status_code=404, detail="No images found.")

        # Encode images as base64
        encoded_images = [base64.b64encode(img).decode('utf-8') for img in image_bytes_list]

        # Clean up the temporary file
        try:
            temp_file_path.unlink()
        except OSError as e:
            print(f"Error deleting temporary file {temp_file_path}: {e}")

        return JSONResponse(content={"images": encoded_images})

    except Exception as e:
        print(f"Error in refine_first_gen: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/refine_object")
def refine_object(request: RefineObjectRequest):
    try:
        # Load the workflow template
        workflow_path = WORKFLOWS_DIR / "object_refine_workflow_api.json"
        workflow_data = json.loads(workflow_path.read_text())

        # Decode and save the input image
        image_data = base64.b64decode(request.image)
        temp_file_name = f"{request.gen_id}_temp_input.png"
        temp_file_path = INPUT_DIR / temp_file_name

        with temp_file_path.open("wb") as f:
            f.write(image_data)

        # Insert the original prompt
        workflow_data["214"]["inputs"]["text"] = request.original_prompt

        # Use the temporary file as input
        workflow_data["47"]["inputs"]["image"] = temp_file_name

        # Insert the prompt if it's used in this workflow
        if "6" in workflow_data and "inputs" in workflow_data["6"]:
            workflow_data["6"]["inputs"]["text"] = request.prompt

        # Set the filename prefix
        workflow_data["164"]["inputs"]["filename_prefix"] = f"{request.gen_id}_refine_object"

        # Save the modified workflow
        new_workflow_file = WORKFLOWS_DIR / f"{request.gen_id}_refine_object.json"
        with new_workflow_file.open("w") as f:
            json.dump(workflow_data, f)

        # Run the workflow
        run_comfy_command(f"comfy run --workflow {new_workflow_file} --wait --verbose --timeout 1200")

        # Retrieve output images
        image_bytes_list = find_output_images(f"{request.gen_id}_refine_object")

        if not image_bytes_list:
            raise HTTPException(status_code=404, detail="No images found.")

        # Encode images as base64
        encoded_images = [base64.b64encode(img).decode('utf-8') for img in image_bytes_list]

        # Clean up the temporary file
        try:
            temp_file_path.unlink()
        except OSError as e:
            print(f"Error deleting temporary file {temp_file_path}: {e}")

        return JSONResponse(content={"images": encoded_images})

    except Exception as e:
        print(f"Error in refine_object: {e}")
        raise HTTPException(status_code=500, detail=str(e))

