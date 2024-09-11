import httpx
from fastapi import HTTPException
import base64
import random
import asyncio
from typing import Callable, Any

class ModalService:
    async def _make_dual_requests(self, url: str, payload: dict, process_response: Callable[[dict], Any]) -> Any:
        results = await asyncio.gather(self._make_request(url, payload, process_response), self._make_request(url, payload, process_response))
        successful_result = next((result for result in results if result is not None), None)

        if successful_result:
            return successful_result
        else:
            raise HTTPException(status_code=500, detail="Both requests failed")
        
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
        url = "https://christopherhwood--product-shoot-comfyui-first-gen.modal.run"
        
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

            return await self._make_request(url, payload, process_response)

        # Generate 'count' number of images using individual requests
        image_data_list = await asyncio.gather(*[single_image_request() for _ in range(count)])
        
        # Flatten the list of lists and remove any None values
        all_images = [img for sublist in image_data_list if sublist for img in sublist]

        if not all_images:
            raise HTTPException(status_code=500, detail="All image generation requests failed")

        return all_images

    async def refine_image(self, image_data: bytes, prompt: str, gen_id: str) -> list[bytes]:
        """
        Send a request to refine an image using the Modal service.

        Args:
            image_data (bytes): The image data to refine.
            prompt (str): The prompt for image refinement.
            gen_id (str): The generation ID.
            noise_strength (float, optional): The strength of noise to inject. Defaults to 0.
            denoise_amount (float, optional): The amount of denoising to apply. Defaults to 0.9.

        Returns:
            list[bytes]: A list of refined image data.

        Raises:
            HTTPException: If the request fails or returns an unexpected status code.
        """
        url = "https://christopherhwood--product-shoot-comfyui-refine-object.modal.run"
        seed = random.randint(0, 2**32 - 1)
        payload = {
            "prompt": 'A photo of a can of Calm Crunchy sparkling water. From top to bottom, the label reads "SPARKLING ADAPTOGENIC WATER" around the white strip at the top, then on the blue background: "CRUNCHY", logo, "HYDRATION", "CALM", "watermelon", "vegan & gluten-free", "12 FL OZ (355 ML)"',
            "original_prompt": prompt,
            "gen_id": gen_id,
            "seed": seed,
            "image": base64.b64encode(image_data).decode('utf-8')
        }

        def process_response(json_response: dict) -> list[bytes]:
            if 'images' in json_response:
                return [base64.b64decode(img) for img in json_response['images']]
            return None

        return await self._make_request(url, payload, process_response)
