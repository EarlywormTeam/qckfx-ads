import httpx
from fastapi import HTTPException
import base64
import random
import asyncio
from typing import Callable, Any

class ModalService:
    async def _make_dual_requests(self, url: str, payload: dict, process_response: Callable[[dict], Any]) -> Any:
        async def make_request():
            async with httpx.AsyncClient(follow_redirects=True) as client:
                try:
                    response = await client.post(url, json=payload, timeout=300.0)
                    if response.status_code == 200:
                        json_response = response.json()
                        return process_response(json_response)
                except httpx.RequestError:
                    pass
            return None

        results = await asyncio.gather(make_request(), make_request())
        successful_result = next((result for result in results if result is not None), None)

        if successful_result:
            return successful_result
        else:
            raise HTTPException(status_code=500, detail="Both requests failed")

    async def generate_images(self, prompt: str, count: int, product_id: str, gen_id: str) -> list[bytes]:
        """
        Send a request to generate images using the Modal service.

        Args:
            prompt (str): The prompt for image generation.
            count (int): The number of images to generate in a batch.
            product_id (str): The ID of the product.
            gen_id (str): The generation ID.

        Returns:
            list[bytes]: A list of generated image data.

        Raises:
            HTTPException: If the request fails or returns an unexpected status code.
        """
        url = "https://christopherhwood--product-shoot-comfyui-first-gen.modal.run"
        seed = random.randint(0, 2**32 - 1)
        payload = {
            "prompt": prompt,
            "count": count,
            "product_id": product_id,
            "gen_id": gen_id,
            "seed": seed
        }

        def process_response(json_response: dict) -> list[bytes]:
            if 'images' in json_response:
                return [base64.b64decode(img) for img in json_response['images']]
            return None

        return await self._make_dual_requests(url, payload, process_response)

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

        return await self._make_dual_requests(url, payload, process_response)
