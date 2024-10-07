import httpx
from fastapi import HTTPException
import base64
import random
import asyncio
import json
from typing import Callable, Any, AsyncGenerator, Optional
from collections import deque

from toolbox.services.flags import FeatureFlags

class ComfyService:
    def __init__(self, flags: FeatureFlags):
        self.flags = flags
        self.default_base_urls = json.loads('{ \
            "urls": [ \
                "https://earlywormteam--product-shoot-comfyui.modal.run", \
                "https://earlywormteam--product-shoot-comfyui.modal.run", \
                "https://earlywormteam--product-shoot-comfyui.modal.run", \
                "https://earlywormteam--product-shoot-comfyui.modal.run" \
            ] \
        }')
        self.gpu_base_urls = flags.get_flag("gpu_base_urls", self.default_base_urls)["urls"]
        self.default_generate_urls = json.loads('{ \
            "urls": [ \
                "https://earlywormteam--product-shoot-comfyui-first-gen.modal.run", \
                "https://earlywormteam--product-shoot-comfyui-first-gen.modal.run", \
                "https://earlywormteam--product-shoot-comfyui-first-gen.modal.run", \
                "https://earlywormteam--product-shoot-comfyui-first-gen.modal.run" \
            ] \
        }')
        self.default_simple_generate_urls = json.loads('{ \
            "urls": [ \
                "https://earlywormteam--product-shoot-comfyui-simple-gen.modal.run", \
                "https://earlywormteam--product-shoot-comfyui-simple-gen.modal.run", \
                "https://earlywormteam--product-shoot-comfyui-simple-gen.modal.run", \
                "https://earlywormteam--product-shoot-comfyui-simple-gen.modal.run" \
            ] \
        }')
        self.url_queues = [asyncio.Queue() for _ in self.gpu_base_urls]
        self.workers = []
        for idx, url in enumerate(self.gpu_base_urls):
            worker = asyncio.create_task(self._queue_worker(idx, url))
            self.workers.append(worker)

    async def _queue_worker(self, queue_index: int, url: str):
        """
        Worker that processes requests from its assigned queue one at a time.
        
        Args:
            queue_index (int): The index of the queue in the url_queues list.
            url (str): The URL endpoint associated with this queue.
        """
        queue = self.url_queues[queue_index]
        while True:
            payload, process_response, future = await queue.get()
            try:
                response = await self._make_request(url, payload, process_response)
                future.set_result(response)
            except Exception as e:
                future.set_exception(e)
            finally:
                queue.task_done()

    async def _enqueue_request(self, payload: dict, process_response: Callable[[dict], Any]) -> Any:
        """
        Enqueue a request to the first available queue.
        
        Args:
            payload (dict): The payload to send in the request.
            process_response (Callable[[dict], Any]): Function to process the JSON response.
        
        Returns:
            Any: The processed response.
        """
        # Simple round-robin assignment
        queue_index = random.randint(0, len(self.url_queues) - 1)
        queue = self.url_queues[queue_index]
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        await queue.put((payload, process_response, future))
        return await future

    async def _make_request(self, url: str, payload: dict, process_response: Callable[[dict], Any]) -> Any:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                response = await client.post(url, json=payload, timeout=400.0)
                if response.status_code == 200:
                    json_response = response.json()
                    return process_response(json_response)
            except httpx.RequestError:
                pass
        return None

    async def generate_images(self, prompt: str, count: int, product_id: str, gen_id: str, lora_name: str, product_description: str, trigger_word: str, detection_prompt: str) -> list[bytes]:
        """
        Send multiple requests to generate images using the Modal service.

        Args:
            prompt (str): The prompt for image generation.
            count (int): The number of images to generate (one per request).
            product_id (str): The ID of the product.
            gen_id (str): The generation ID.
            lora_name (str): The name of the lora weights to use.
            product_description (str): The description of the product.
            trigger_word (str): The trigger word to use for the prompt.

        Returns:
            list[bytes]: A list of generated image data.

        Raises:
            HTTPException: If all requests fail or return unexpected status codes.
        """
        urls = self.flags.get_flag("gpu_urls", self.default_urls)["urls"]
        if count > len(urls):
            raise HTTPException(status_code=400, detail=f"Count exceeds available URLs. Maximum count is {len(urls)}")

        async def single_image_request():
            seed = random.randint(0, 2**32 - 1)
            payload = {
                "prompt": "flux_realism " + prompt,
                "count": 1,  # Always set to 1 for individual image generation
                "product_id": product_id,
                "gen_id": gen_id,
                "seed": seed,
                "lora_name": lora_name,
                "product_description": product_description,
                "trigger_word": trigger_word,
                "detection_prompt": detection_prompt
            }

            def process_response(json_response: dict) -> list[bytes]:
                if 'images' in json_response and json_response['images']:
                    return [base64.b64decode(json_response['images'][0])]
                return None

            return await self._enqueue_request(payload, process_response)

        # Generate 'count' number of images using individual requests
        image_data_list = await asyncio.gather(*[single_image_request() for _ in range(count)])
        
        # Flatten the list of lists and remove any None values
        all_images = [img for sublist in image_data_list if sublist for img in sublist]

        if not all_images:
            raise HTTPException(status_code=500, detail="All image generation requests failed")

        return all_images

    async def refine_image(self, image_data: bytes, original_prompt: str, product_description: str, gen_id: str) -> list[bytes]:
        """
        Send a request to refine an image using the Modal service.

        Args:
            image_data (bytes): The image data to refine.
            original_prompt (str): The original prompt used for image generation.
            product_description (str): The product description for refinement.
            gen_id (str): The generation ID.

        Returns:
            list[bytes]: A list of refined image data.

        Raises:
            HTTPException: If the request fails or returns an unexpected status code.
        """
        seed = random.randint(0, 2**32 - 1)
        payload = {
            "prompt": product_description,  # Use the product description as the main prompt
            "original_prompt": original_prompt,  # Include the original prompt
            "gen_id": gen_id,
            "seed": seed,
            "image": base64.b64encode(image_data).decode('utf-8')
        }

        def process_response(json_response: dict) -> list[bytes]:
            if 'images' in json_response:
                return [base64.b64decode(img) for img in json_response['images']]
            return None

        return await self._enqueue_request(payload, process_response)
    
    async def generate_simple_images_stream(self, prompt: str, count: int, product_id: str, gen_id: str, lora_name: str) -> AsyncGenerator[tuple[int, bytes | None], None]:
        urls = self.flags.get_flag("simple_generate_urls", self.default_simple_generate_urls)["urls"]
        if count > len(urls):
            raise HTTPException(status_code=400, detail=f"Count exceeds available URLs. Maximum count is {len(urls)}")

        async def single_image_request(index: int):
            seed = random.randint(0, 2**32 - 1)
            payload = {
                "prompt": prompt,
                "count": 1,  # Always set to 1 for individual image generation
                "product_id": product_id,
                "gen_id": gen_id,
                "seed": seed,
                "lora_name": lora_name
            }

            def process_response(json_response: dict) -> Optional[bytes]:
                if 'images' in json_response and json_response['images']:
                    return base64.b64decode(json_response['images'][0])
                return None

            result = await self._enqueue_request(payload, process_response)
            return index, result

        tasks = [single_image_request(i) for i in range(count)] 
        for task in asyncio.as_completed(tasks):
            result = await task
            yield result

    async def generate_images_stream(self, prompt: str, count: int, product_id: str, gen_id: str, lora_name: str, product_description: str, trigger_word: str, detection_prompt: str, image_name: Optional[str] = None) -> AsyncGenerator[tuple[int, bytes | None], None]:
        """
        Send multiple requests to generate images using the Modal service and yield them as they are created.

        Args:
            prompt (str): The prompt for image generation.
            count (int): The number of images to generate (one per request).
            product_id (str): The ID of the product.
            gen_id (str): The generation ID.
            lora_name (str): The name of the lora weights to use.
            product_description (str): The description of the product.
            trigger_word (str): The trigger word to use for the prompt.
            detection_prompt (str): The detection prompt for the image.

        Yields:
            tuple[int, bytes | None]: A tuple containing the index of the generated image and the image data.

        Raises:
            HTTPException: If all requests fail or return unexpected status codes.
        """
        urls = self.flags.get_flag("gpu_urls", self.default_generate_urls)["urls"]
        if count > len(urls):
            raise HTTPException(status_code=400, detail=f"Count exceeds available URLs. Maximum count is {len(urls)}")
        
        async def single_image_request(index: int):
            seed = random.randint(0, 2**32 - 1)
            payload = {
                "prompt": prompt,
                "count": 1,  # Always set to 1 for individual image generation
                "product_id": product_id,
                "gen_id": gen_id,
                "seed": seed,
                "lora_name": lora_name,
                "product_description": product_description,
                "trigger_word": trigger_word,
                "detection_prompt": detection_prompt,
                "image_name": image_name
            }

            def process_response(json_response: dict) -> Optional[bytes]:
                if 'images' in json_response and json_response['images']:
                    return base64.b64decode(json_response['images'][0])
                return None

            return await self._enqueue_request(payload, process_response)

        tasks = [single_image_request(i) for i in range(count)]
        for task in asyncio.as_completed(tasks):
            result = await task
            yield result
