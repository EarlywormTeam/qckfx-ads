import os
from dotenv import load_dotenv
import replicate
import fal_client
from .modal import ModalService  # Import ModalService

class ImageService:
    def __init__(self):
        load_dotenv()
        self.replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))
        self.fal_key = os.getenv("FAL_KEY")
        self.modal_service = ModalService()  # Create an instance of ModalService

    async def remove_background(self, image_url):
        try:
            output = await self.client.async_run(
                "smoretalk/rembg-enhance:4067ee2a58f6c161d434a9c077cfa012820b8e076efa2772aa171e26557da919",
                input={"image": image_url}
            )
            return output
        except Exception as e:
            raise Exception(f"Error in background removal: {str(e)}")

    async def finetune_model(self, images_data_url, steps=1000, rank=16, learning_rate=0.0004,
                             caption_dropout_rate=0.05, trigger_word=None, captions_file_url=None,
                             experimental_optimizers="adamw8bit", experimental_multi_checkpoints_count=1,
                             experimental_multi_checkpoints_interval=None):
        try:
            arguments = {
                "images_data_url": images_data_url,
                "steps": steps,
                "rank": rank,
                "learning_rate": learning_rate,
                "caption_dropout_rate": caption_dropout_rate,
                "experimental_optimizers": experimental_optimizers,
                "experimental_multi_checkpoints_count": experimental_multi_checkpoints_count
            }

            if trigger_word:
                arguments["trigger_word"] = trigger_word
            if captions_file_url:
                arguments["captions_file_url"] = captions_file_url
            if experimental_multi_checkpoints_interval:
                if experimental_multi_checkpoints_interval > 250:
                    arguments["experimental_multi_checkpoints_interval"] = experimental_multi_checkpoints_interval
                else:
                    raise ValueError("experimental_multi_checkpoints_interval must be greater than 250")

            handler = await fal_client.submit_async(
                "fal-ai/flux-lora-general-training",
                arguments=arguments,
                api_key=self.fal_key
            )
            result = await handler.get()
            
            # Process the result
            processed_result = {
                "diffusers_lora_file": result.get("diffusers_lora_file", {}).get("url", ""),
                "config_file": result.get("config_file", {}).get("url", ""),
                "debug_caption_files": result.get("debug_caption_files", {}).get("url", ""),
                "experimental_multi_checkpoints": [
                    checkpoint.get("url", "") for checkpoint in result.get("experimental_multi_checkpoints", [])
                ]
            }
            
            return processed_result
        except Exception as e:
            raise Exception(f"Error in model fine-tuning: {str(e)}")

    async def generate_images(self, prompt: str, count: int, product_id: str, gen_id: str, lora_name: str, product_description: str, trigger_word: str, detection_prompt: str) -> list:
        """
        Generate images using the Modal service.

        Args:
            prompt (str): The prompt for image generation.
            count (int): The number of images to create in a batch.
            product_id (str): The ID of the product.
            gen_id (str): The generation ID.

        Returns:
            list: A list of base64-encoded image strings.

        Raises:
            Exception: If there's an error during image generation.
        """
        try:
            result = await self.modal_service.generate_images(prompt, count, product_id, gen_id, lora_name, product_description, trigger_word, detection_prompt)
            return result
        except Exception as e:
            raise Exception(f"Error in image generation: {str(e)}")

    async def refine_image(self, image_data: bytes, prompt: str, gen_id: str) -> list[bytes]:
        """
        Refine an image using the Modal service.

        Args:
            image_data (bytes): The image data to refine.
            prompt (str): The prompt for image refinement.
            gen_id (str): The generation ID.
            noise_strength (float, optional): The strength of noise to inject. Defaults to 0.
            denoise_amount (float, optional): The amount of denoising to apply. Defaults to 0.9.

        Returns:
            list[bytes]: A list of refined image data.

        Raises:
            Exception: If there's an error during image refinement.
        """
        try:
            result = await self.modal_service.refine_image(image_data, prompt, gen_id)
            return result
        except Exception as e:
            raise Exception(f"Error in image refinement: {str(e)}")

# Usage example:
# image_service = ImageService()
# result = await image_service.remove_background("https://example.com/image.jpg")
# print(result)
