# main.py
import json
import os
import shutil
import subprocess
import time
import socket
import sys
import re
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
    image_name: str

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
    """Run a ComfyUI command and stream output in real-time."""
    process = subprocess.Popen(
        cmd,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,  # Ensures the output is decoded to string
        bufsize=1,  # Line-buffered
        universal_newlines=True
    )

    # Stream stdout
    while True:
        stdout_line = process.stdout.readline()
        if stdout_line:
            print(stdout_line, end='')  # Print stdout lines as they come
        else:
            break

    # Stream stderr
    while True:
        stderr_line = process.stderr.readline()
        if stderr_line:
            print(stderr_line, end='', file=sys.stderr)  # Print stderr lines as they come
        else:
            break

    process.stdout.close()
    process.stderr.close()
    return_code = process.wait()

    if return_code != 0:
        raise RuntimeError(f"Command failed with return code {return_code}")

def is_port_open(port, host='localhost'):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((host, port))
            return True
        except socket.error:
            return False

def find_output_images(file_prefix: str) -> List[bytes]:
    """Find and return image bytes from the output directory based on the file prefix."""
    image_bytes_list = []
    for f in OUTPUT_DIR.iterdir():
        if f.is_file() and f.name.startswith(file_prefix):
            image_bytes_list.append(f.read_bytes())
    return image_bytes_list

def launch_comfyui():
    """Launch ComfyUI as a subprocess."""
    cmd = f"comfy --skip-prompt --workspace={COMFYUI_DIR} launch --background -- --highvram --cuda-device=0"
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True, cwd=COMFYUI_DIR)
  
    check_interval = 1
    port = 8188
    timeout = 300 # 5 mins
    start_time = time.time()
    while time.time() - start_time < timeout:
        # Check if the process is still running
        if process.poll() is not None:
            raise Exception("ComfyUI process terminated unexpectedly")

        # Check for specific log message
        line = process.stdout.readline()
        if "To see the GUI go to" in line:
            print("ComfyUI startup message detected")
            break

        # Check if the port is open
        if is_port_open(port):
            print(f"Port {port} is open")
            break

        time.sleep(check_interval)
    else:
        process.terminate()
        raise TimeoutError("ComfyUI startup timed out")

    print("ComfyUI is up and running")

# Event Handlers
@app.on_event("startup")
def startup_event():
    """Launch ComfyUI when the FastAPI app starts."""
    try:
        subprocess.run("curl --silent http://localhost:8080", shell=True, check=True)
        print("ComfyUI is already running.")
    except subprocess.CalledProcessError:
        launch_comfyui()

# API Endpoints
@app.post("/first_gen")
def first_gen(request: FirstGenRequest):
    print(f"first_gen {request.gen_id}")
    try:
        launch_comfyui()
        # Load the workflow template
        workflow_path = WORKFLOWS_DIR / "first_gen_workflow_api.json"
        workflow_data = json.loads(workflow_path.read_text())

        # Modify the workflow based on the request
        workflow_data["295"]["inputs"]["text"] = f"{request.trigger_word} {request.prompt}"
        workflow_data["483"]["inputs"]["Text"] = f"{request.trigger_word} {request.prompt}"
 
        # Set the number of images to generate
        workflow_data["304"]["inputs"]["batch_size"] = request.count

        # Set the filename prefix
        workflow_data["164"]["inputs"]["filename_prefix"] = f"{request.gen_id}_{request.seed}_first_gen_1"
        # workflow_data["698"]["inputs"]["filename_prefix"] = f"{request.gen_id}_{request.seed}_first_gen_2"

        # Set the lora
        workflow_data["125"]["inputs"]["lora_name"] = request.lora_name
        workflow_data["329"]["inputs"]["lora_name"] = request.lora_name
        workflow_data["574"]["inputs"]["lora_name"] = request.lora_name

        # Set the product description
        workflow_data["511"]["inputs"]["Text"] = request.product_description

        workflow_data["130"]["inputs"]["image"] = request.image_name

        # Set the detection prompt
        detection_nodes = ["120", "128", "168", "266", "283", "425", "468", "556", "563", "596", "651", "666", ]
        for node_id in detection_nodes:
            workflow_data[node_id]["inputs"]["prompt"] = request.detection_prompt

        # Set the seed
        seed_nodes = ["25", "192", "212", "236", "303", "661"]
        for node_id in seed_nodes:
            workflow_data[node_id]["inputs"]["noise_seed"] = request.seed

        # Save the modified workflow
        new_workflow_file = WORKFLOWS_DIR / f"{request.gen_id}_{request.seed}_first_gen.json"
        with new_workflow_file.open("w") as f:
            json.dump(workflow_data, f)

        # Run the workflow
        print(f"starting comfy run {request.gen_id}")
        run_comfy_command(f"comfy run --workflow {new_workflow_file} --wait --verbose --timeout 150")
        print(f"finished comfy run {request.gen_id}")

        # Retrieve output images
        image_bytes_list = find_output_images(f"{request.gen_id}_{request.seed}_first_gen")

        if not image_bytes_list:
            raise HTTPException(status_code=404, detail="No images found.")

        # Encode images as base64
        encoded_images = [base64.b64encode(img).decode('utf-8') for img in image_bytes_list]

        run_comfy_command("comfy stop")

        return JSONResponse(content={"images": encoded_images})

    except Exception as e:
        print(f"Error in first_gen: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ping")
def ping():
    run_comfy_command("comfy env")
    return JSONResponse(content={"status": "ok"})

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
        run_comfy_command(f"comfy run --workflow {new_workflow_file} --wait --verbose --timeout 150")

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
        run_comfy_command(f"comfy run --workflow {new_workflow_file} --wait --verbose --timeout 150")

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

