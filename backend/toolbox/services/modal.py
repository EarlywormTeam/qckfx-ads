import httpx
from fastapi import HTTPException
import base64
import random

class ModalService:
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
        payload = {
            "prompt": prompt,
            "count": count,
            "product_id": product_id,
            "gen_id": gen_id,
            "seed": random.randint(0, 2**32 - 1)
        }

        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                # Timeout of 300 seconds (5 minutes) because cold starts are > 2min and cold execution is ~1.5 mins.
                response = await client.post(url, json=payload, timeout=300.0)
                
                # Check if the final response is successful
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=f"Request failed with status code: {response.status_code}")

                # Parse the JSON response
                json_response = response.json()
                
                # Check if 'images' key exists in the response
                if 'images' not in json_response:
                    raise HTTPException(status_code=500, detail="Unexpected response format: 'images' key not found")

                # Decode base64 encoded images
                decoded_images = [base64.b64decode(img) for img in json_response['images']]
                
                return decoded_images
            except httpx.RequestError as e:
                raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
