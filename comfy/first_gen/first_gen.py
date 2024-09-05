# ---
# cmd: ["modal", "serve", "06_gpu_and_ml/comfyui/comfyapp.py"]
# deploy: true
# ---

#
# # Run ComfyUI interactively and as an API
#
# [ComfyUI](https://github.com/comfyanonymous/ComfyUI) is a no-code Stable Diffusion GUI that allows you to design and execute advanced image generation pipelines.
#
# ![example comfyui image](./comfyui.png)
#
# In this example, we show you how to
#
# 1. run ComfyUI interactively to develop workflows
#
# 2. serve a ComfyUI workflow as an API
#
# Combining the UI and the API in a single app makes it easy to iterate on your workflow even after deployment.
# Simply head to the interactive UI, make your changes, export the JSON, and redeploy the app.
#
# ## Quickstart
#
# This example serves the [ComfyUI inpainting example workflow](https://comfyanonymous.github.io/ComfyUI_examples/inpaint/),
# which "fills in" part of an input image based on a prompt.
# For the prompt `"Spider-Man visits Yosemite, rendered by Blender, trending on artstation"`
# on [this input image](https://raw.githubusercontent.com/comfyanonymous/ComfyUI_examples/master/inpaint/yosemite_inpaint_example.png),
# we got this output:
#
# ![example comfyui image](./comfyui_gen_image.jpg)
#
# 1. Stand up the ComfyUI server in development mode:
# ```bash
# modal serve 06_gpu_and_ml/comfyui/comfyapp.py
# ```
#
# 2. In another terminal, run inference:
# ```bash
# python 06_gpu_and_ml/comfyui/comfyclient.py --dev --modal-workspace your-modal-workspace --prompt "your prompt here"
# ```
# You can find your Modal workspace name by running `modal profile current`.
#
# The first inference will take a bit longer because the server will need to boot up (~20-30s).
# Successive inference calls while the server is up should take a few seconds or less.
#
# ## Setup
#
# First, we define the environment we need to run ComfyUI using [comfy-cli](https://github.com/Comfy-Org/comfy-cli). This handy tool manages the installation of ComfyUI, its dependencies, models, and custom nodes.


import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict

import modal


image = (  # build up a Modal Image to run ComfyUI, step by step
    modal.Image.debian_slim(  # start from basic Linux with Python
        python_version="3.11"
    )
    .apt_install("git", "wget")  # install git to clone ComfyUI
    .pip_install("comfy-cli==1.1.6", "python-dotenv")  # install comfy-cli
    .run_commands(  # use comfy-cli to install the ComfyUI repo and its dependencies
        "comfy --skip-prompt install --nvidia",
    )
    .run_commands(  # download the inpainting model
        f"wget --header=\"Authorization: Bearer {os.getenv('HF_TOKEN')}\" -P /root/comfy/ComfyUI/models/unet https://huggingface.co/black-forest-labs/FLUX.1-dev/resolve/main/flux1-dev.safetensors"
    )
    .run_commands(
        "comfy --skip-prompt model download --url https://huggingface.co/black-forest-labs/FLUX.1-schnell/resolve/main/ae.safetensors --relative-path models/vae",
        "comfy --skip-prompt model download --url https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors --relative-path models/clip",
        "comfy --skip-prompt model download --url https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp16.safetensors --relative-path models/clip",
        "wget --header=\"Authorization: Bearer {os.getenv('REPLICATE_API_TOKEN')}\" -P /models/loras/med_intense_can https://replicate.delivery/yhqm/QRnYk8tBa84yCtjZC4ZfpJB4pHKL3vgZoVJwhOYqhpc6eEXTA/trained_model.tar",
        "tar -xvf /models/loras/med_intense_can/trained_model.tar -C /models/loras/med_intense_can",
        "mv /models/loras/med_intense_can/output/flux_train_replicate/lora.safetensors /root/comfy/ComfyUI/models/loras/med_intense_can.safetensors && rm -rf /models"
    )
    .run_commands(  # download a custom node
        "comfy node install comfyui_segment_anything",
        "comfy node install x-flux-comfyui",
        "comfy node install Jovimetrix",
        "comfy node install ComfyUI_Comfyroll_CustomNodes",
        "comfy node install rgthree-comfy",
        "comfy node install comfyui_controlnet_aux"
    )
    .run_commands(
        "comfy node install ComfyUI_essentials"
    )
    .run_commands(
        "comfy node install ComfyUI-Impact-Pack",
        "comfy node install Derfuu_ComfyUI_ModdedNodes",
        "comfy node install was-node-suite-comfyui",
        "comfy node install comfyui-various",
        "comfy node install ComfyUI-Image-Filters",
        "comfy node install ComfyUI-KJNodes",
        "comfy node install comfyui-mixlab-nodes"
    )
    .run_commands(
        "comfy --skip-prompt model download --url https://huggingface.co/XLabs-AI/flux-controlnet-collections/resolve/main/flux-canny-controlnet_v2.safetensors --relative-path models/xlabs/controlnets",
        "cp root/comfy/ComfyUI/models/xlabs/controlnets/flux-canny-controlnet_v2.safetensors root/comfy/ComfyUI/models/controlnet/controlnet.safetensors"
    )
    # can layer additional models and custom node downloads as needed
)

app = modal.App(name="product-shoot", image=image)


## Running ComfyUI interactively and as an API on Modal

# To run ComfyUI interactively, simply wrap the `comfy launch` command in a Modal Function and serve it as a web server.
# @app.function(
#     allow_concurrent_inputs=10,
#     concurrency_limit=1,
#     container_idle_timeout=30,
#     timeout=1800,
#     gpu="a100",
#     mounts=[
#         modal.Mount.from_local_file(
#             Path(__file__).parent / "image-registration-node.py",
#             "/root/comfy/ComfyUI/custom_nodes/image-registration-node.py"
#         ),
#     ],
# )
# @modal.web_server(8000, startup_timeout=180)
# def ui():
#     subprocess.Popen("comfy launch -- --listen 0.0.0.0 --port 8000", shell=True)

# Remember to **close your UI tab** when you are done developing to avoid accidental charges to your account.
# This will close the connection with the container serving ComfyUI, which will spin down based on your `container_idle_timeout` setting.
#
# To run an existing workflow as an API, we use Modal's class syntax to run our customized ComfyUI environment and workflow on Modal.
#
# Here's the basic breakdown of how we do it:
# 1. We stand up a "headless" ComfyUI server in the background when the app starts.
# 2. We define an `infer` method that takes in a workflow path and runs the workflow on the ComfyUI server.
# 3. We stand up an `api` with `web_endpoint`, so that we can run our workflows as a service.
#
# For more on how to run web services on Modal, check out [this guide](https://modal.com/docs/guide/webhooks).
@app.cls(
    allow_concurrent_inputs=10,
    concurrency_limit=1,
    container_idle_timeout=300,
    gpu="h100",
    mounts=[
        modal.Mount.from_local_file(
            Path(__file__).parent / "first_gen_workflow_api.json",
            "/root/first_gen_workflow_api.json",
        ),
        modal.Mount.from_local_file(
            Path(__file__).parent / "refined_first_gen_workflow_api.json",
            "/root/refined_first_gen_workflow_api.json",
        ),
        modal.Mount.from_local_file(
            Path(__file__).parent / "object_refining_workflow_api.json",
            "/root/object_refining_workflow_api.json",
        ),
        modal.Mount.from_local_file(
            Path(__file__).parent / "image-registration-node.py",
            "/root/comfy/ComfyUI/custom_nodes/image-registration-node.py"
        ),
        # mount input images
        modal.Mount.from_local_file(
            Path(__file__).parent / "can.png",
            "/root/comfy/ComfyUI/input/can.png",
        ),
    ],
)
class ComfyUI:
    @modal.enter()
    def launch_comfy_background(self):
        cmd = "comfy launch --background"
        subprocess.run(cmd, shell=True, check=True)

    @modal.method()
    def infer(self, workflow_path: str = "/root/first_gen_workflow_api.json"):
        # runs the comfy run --workflow command as a subprocess
        cmd = f"comfy run --workflow {workflow_path} --wait --timeout 1200"
        subprocess.run(cmd, shell=True, check=True)

        # completed workflows write output images to this directory
        output_dir = "/root/comfy/ComfyUI/output"
        # looks up the name of the output image file based on the workflow
        workflow = json.loads(Path(workflow_path).read_text())
        file_prefix = [
            node.get("inputs")
            for node in workflow.values()
            if node.get("class_type") == "SaveImage"
        ][0]["filename_prefix"]

        # returns a list of image bytes
        image_bytes_list = []
        for f in Path(output_dir).iterdir():
            if f.name.startswith(file_prefix):
                image_bytes_list.append(f.read_bytes())
        return image_bytes_list

    @modal.method()
    def find_output(self, file_prefix):
        output_dir = "/root/comfy/ComfyUI/output"

        for f in Path(output_dir).iterdir():
            if f.name.startswith(file_prefix):
                return f.name

    @modal.method()
    def move_output_to_input(self, file_name):
        output_dir = "/root/comfy/ComfyUI/output"
        input_dir = "/root/comfy/ComfyUI/input"
        shutil.copy(f"{output_dir}/{file_name}", f"{input_dir}/{file_name}")

    @modal.web_endpoint(method="POST")
    def first_gen(self, item: Dict):
        from fastapi.responses import JSONResponse
        import base64

        workflow_data = json.loads(
            (Path(__file__).parent / "first_gen_workflow_api.json").read_text()
        )
        gen_id = item["gen_id"]

        # insert the prompt
        workflow_data["6"]["inputs"]["text"] = item["prompt"]

        # set the number of images to generate
        workflow_data["149"]["inputs"]["batch_size"] = item["count"]

        # give the output image a unique id per client request
        workflow_data["9"]["inputs"]["filename_prefix"] = f"{gen_id}_first_gen"

        # set the seed
        workflow_data["148"]["inputs"]["seed"] = item["seed"]

        # save this updated workflow to a new file
        new_workflow_file = f"{gen_id}_first_gen.json"
        json.dump(workflow_data, Path(new_workflow_file).open("w"))

        # run inference on the currently running container
        img_bytes_list = self.infer.local(new_workflow_file)

        # Always return images as a JSON array of base64 encoded strings
        encoded_images = [base64.b64encode(img).decode('utf-8') for img in img_bytes_list]
        return JSONResponse(content={"images": encoded_images})


    @modal.web_endpoint(method="POST")
    def refine_first_gen(self, item: Dict):
        from fastapi.responses import JSONResponse
        import base64

        workflow_data = json.loads(
            (Path(__file__).parent / "refined_first_gen_workflow_api.json").read_text()
        )
        gen_id = item["gen_id"]

        # Decode the base64 encoded image from the request body
        image_data = base64.b64decode(item["image"])

        # Save the decoded image to a temporary file in the input directory
        input_dir = "/root/comfy/ComfyUI/input"
        temp_file_name = f"{gen_id}_temp_input.png"
        temp_file_path = f"{input_dir}/{temp_file_name}"
        
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(image_data)

        # Use the temporary file as input for the workflow
        workflow_data["47"]["inputs"]["image"] = temp_file_name

        # set the noise injection
        noise_strength = item.get("noise_strength", 0)
        workflow_data["158"]["inputs"]["noise_strength"] = noise_strength

        denoise_amount = item.get("denoise_amount", 0.9)
        workflow_data["17"]["inputs"]["denoise"] = denoise_amount

        # insert the prompt
        workflow_data["6"]["inputs"]["text"] = item["prompt"]

        # give the output image a unique id per client request
        workflow_data["165"]["inputs"]["filename_prefix"] = f"{gen_id}_refine_first_gen"

        # save this updated workflow to a new file
        new_workflow_file = f"{gen_id}_refine_first_gen.json"
        json.dump(workflow_data, Path(new_workflow_file).open("w"))

        # run inference on the currently running container
        img_bytes_list = self.infer.local(new_workflow_file)

        # Always return images as a JSON array of base64 encoded strings
        encoded_images = [base64.b64encode(img).decode('utf-8') for img in img_bytes_list]

        # Clean up the temporary file
        try:
            os.remove(temp_file_path)
        except OSError as e:
            print(f"Error deleting temporary file {temp_file_path}: {e}")
        return JSONResponse(content={"images": encoded_images})

    @modal.web_endpoint(method="POST")
    def refine_object(self, item: Dict):
        from fastapi.responses import JSONResponse
        import base64

        workflow_data = json.loads(
            (Path(__file__).parent / "object_refining_workflow_api.json").read_text()
        )
        gen_id = item["gen_id"]

        # Decode the base64 encoded image from the request body
        image_data = base64.b64decode(item["image"])

        # Save the decoded image to a temporary file in the input directory
        input_dir = "/root/comfy/ComfyUI/input"
        temp_file_name = f"{gen_id}_temp_input.png"
        temp_file_path = f"{input_dir}/{temp_file_name}"
        
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(image_data)

        # Use the temporary file as input for the workflow
        workflow_data["47"]["inputs"]["image"] = temp_file_name

         # set the noise injection
        noise_strength = item.get("noise_strength", 0)
        workflow_data["158"]["inputs"]["noise_strength"] = noise_strength

        denoise_amount = item.get("denoise_amount", 0.9)
        workflow_data["17"]["inputs"]["denoise"] = denoise_amount

        # Insert the prompt if it's used in this workflow
        if "6" in workflow_data and "inputs" in workflow_data["6"]:
            workflow_data["6"]["inputs"]["text"] = item.get("prompt", "")

        # Give the output image a unique id per client request
        workflow_data["165"]["inputs"]["filename_prefix"] = f"{gen_id}_refine_object"

        # Save this updated workflow to a new file
        new_workflow_file = f"{gen_id}_refine_object.json"
        json.dump(workflow_data, Path(new_workflow_file).open("w"))

        # Run inference on the currently running container
        img_bytes_list = self.infer.local(new_workflow_file)

        # Always return images as a JSON array of base64 encoded strings
        encoded_images = [base64.b64encode(img).decode('utf-8') for img in img_bytes_list]

        # Clean up the temporary file
        try:
            os.remove(temp_file_path)
        except OSError as e:
            print(f"Error deleting temporary file {temp_file_path}: {e}")

        return JSONResponse(content={"images": encoded_images})

# ### The workflow for developing workflows
#
# When you run this script with `modal deploy 06_gpu_and_ml/comfyui/comfyapp.py`, you'll see a link that includes `ui`.
# Head there to interactively develop your ComfyUI workflow. All of your models and custom nodes specified in the image build step will be loaded in.
#
#
# To serve the workflow after you've developed it, first export it as "API Format" JSON:
# 1. Click the gear icon in the top-right corner of the menu
# 2. Select "Enable Dev mode Options"
# 3. Go back to the menu and select "Save (API Format)"
#
# Save the exported JSON to the `workflow_api.json` file in this directory.
#
# Then, redeploy the app with this new workflow by running `modal deploy 06_gpu_and_ml/comfyui/comfyapp.py` again.
#
# ## Further optimizations
#
# - If you're noticing long startup times for the ComfyUI server (e.g. >30s), this is likely due to too many custom nodes being loaded in. Consider breaking out your deployments into one App per unique combination of models and custom nodes.
# - To reduce image build time, you can write custom code to cache previous model and custom node downloads into a Modal [Volume](https://modal.com/docs/guide/volumes) to avoid full downloads on image rebuilds. (see [gist](https://gist.github.com/kning/bb5f076e831266d00e134fcb3a13ed88)).
# - For those who prefer to run a ComfyUI workflow directly as a Python script, see [this blog post](https://modal.com/blog/comfyui-prototype-to-production).
