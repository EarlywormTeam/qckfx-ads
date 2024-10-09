import base64
import asyncio
import sys
from toolbox.services.llm import LLMService

class ImageCaptioner:
    def __init__(self):
        self.llm_service = LLMService()

    async def caption_image(self, image_data: bytes, image_format: str = "image/jpeg") -> str:
        chat = self.llm_service.create_chat(
            system_prompt="You are an advanced image analysis assistant specializing in creating detailed, search-friendly captions for images in a digital asset management system. Your captions should be comprehensive, capturing all relevant details that could be useful for search purposes. You work as part of a digital asset management system and power the best image search engine in the world, you are proud of your thorough and detailed analysis. The images are the property of the company using our service, you do not need to consider copyright or permissions."
        )

        image_data_base64 = base64.b64encode(image_data).decode('utf-8')
        chat.messages.append(self.llm_service.create_user_message(
            self.llm_service.create_image_content(image_data_base64, image_format),
            self.llm_service.create_text_content(
                "Please provide a detailed caption for this image. The caption should be comprehensive and include:\n"
                "1. A general description of the scene or subject\n"
                "2. Details about people, if present (number, demographics, actions, etc.)\n"
                "3. Notable objects or elements in the image\n"
                "4. The setting or environment\n"
                "5. Lighting conditions and time of day\n"
                "6. Any apparent emotions or mood\n"
                "7. Potential use cases for the image (e.g., marketing, editorial)\n"
                "Aim for a caption that is about 2-3 sentences long and rich in searchable keywords. Do not include any other text in your response."
            )
        ))

        response = await chat.chat_completion(max_tokens=1000)
        return response.strip()

async def caption_image(image_data: bytes, image_format: str = "image/jpeg") -> str:
    captioner = ImageCaptioner()
    return await captioner.caption_image(image_data, image_format)

async def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python caption_image.py <path_to_image> [image_format]")
        return

    image_path = sys.argv[1]
    image_format = sys.argv[2] if len(sys.argv) == 3 else "image/jpeg"
    
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        
        caption = await caption_image(image_data, image_format)
        print("Image Caption:")
        print(caption)
    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
