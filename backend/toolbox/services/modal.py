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
        payload = {
            "prompt": 'A photo of a can of Calm Crunchy sparkling water. From top to bottom, the label reads "SPARKLING ADAPTOGENIC WATER" around the white strip at the top, then on the blue background: "CRUNCHY", logo, "HYDRATION", "CALM", "watermelon", "vegan & gluten-free", "12 FL OZ (355 ML)"',
            "gen_id": gen_id,
            "seed": random.randint(0, 2**32 - 1),
        }

        # Encode the image data to base64
        encoded_image = base64.b64encode(image_data).decode('utf-8')
        payload["image"] = encoded_image

        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                # Timeout of 300 seconds (5 minutes) to account for potential long processing times
                response = await client.post(url, json=payload, timeout=300.0)
                
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=f"Request failed with status code: {response.status_code}")

                json_response = response.json()
                
                if 'images' not in json_response:
                    raise HTTPException(status_code=500, detail="Unexpected response format: 'images' key not found")

                print(f"received {len(json_response['images'])} images")
                # Decode base64 encoded images
                decoded_images = [base64.b64decode(img) for img in json_response['images']]
                
                return decoded_images
            except httpx.RequestError as e:
                raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
