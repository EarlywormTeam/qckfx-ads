import os
from dotenv import load_dotenv
import replicate
import fal_client

class ImageService:
    def __init__(self):
        load_dotenv()
        self.replicate_client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))
        self.fal_key = os.getenv("FAL_KEY")

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

# Usage example:
# image_service = ImageService()
# result = await image_service.remove_background("https://example.com/image.jpg")
# print(result)
