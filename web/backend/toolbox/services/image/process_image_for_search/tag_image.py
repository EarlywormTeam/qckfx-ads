import base64
import json
from pydantic import BaseModel, Field
from typing import List
from toolbox.services.llm import LLMService
import asyncio
import sys

class ImageTags(BaseModel):
    people: List[str] = Field(default_factory=list)
    lighting: List[str] = Field(default_factory=list)
    emotions: List[str] = Field(default_factory=list)
    event: List[str] = Field(default_factory=list)
    objects: List[str] = Field(default_factory=list)
    regions: List[str] = Field(default_factory=list)
    orientation: List[str] = Field(default_factory=list)
    focus: List[str] = Field(default_factory=list)
    time: List[str] = Field(default_factory=list)
    weather: List[str] = Field(default_factory=list)

class ImageTagger:
    def __init__(self):
        self.llm_service = LLMService()

    async def tag_image(self, image_data: bytes, image_format: str = "image/jpeg") -> ImageTags:
        chat = self.llm_service.create_chat(
            system_prompt="You are an image analysis assistant specialized in tagging images with detailed attributes which will be used for a search engine. You work as part of a digital asset management system. The images are the property of the company using our service, you do not need to consider copyrights or permissions. You power the best digital asset management search engine in the world and are thorough and detailed in your analysis."
        )

        image_data_base64 = base64.b64encode(image_data).decode('utf-8')
        chat.messages.append(self.llm_service.create_user_message(
            self.llm_service.create_image_content(image_data_base64, image_format),
            self.llm_service.create_text_content(
                "Analyze this image and provide tags for the following categories:\n"
                "1. People: couple, group, single, age (baby, youth, teen, adult, senior), gender (male, female, non-binary), ethnicity (white, black, asian, latino, native american, etc.), clothing (casual, formal, swimwear, etc.), accessories (jewelry, glasses, hat, etc.), pose (action, dance, etc.)\n"
                "2. Lighting: ambient, daylight, night, studio, strobe, lifestyle, portrait, etc.\n"
                "3. Emotions: happy, sad, angry, gloomy, casual, formal, etc.\n"
                "4. Event: wedding, birthday, graduation, fundraiser, conference, anniversary, etc.\n"
                "5. Objects: furniture, plants, food, drinks, etc.\n"
                "6. Regions: forest, mountains, desert, ocean, building, etc.\n"
                "7. Orientation: portrait, landscape, square\n"
                "8. Focus: macro, close-up, wide, etc.\n"
                "9. Time: morning, afternoon, evening, night\n"
                "10. Weather: sunny, rainy, snowy, windy, cloudy, etc.\n"
                "Provide your answer as a JSON object with these categories as keys and arrays of relevant tags as values. Do not include any other text in your response."
            )
        ))

        response: ImageTags = await chat.chat_completion(max_tokens=3000, pydantic_object=ImageTags)
        print(response.model_dump_json(indent=2))

        if not response:
            print("Error: Invalid JSON response from LLM")
            return ImageTags()

        return response

async def tag_image(image_data: bytes, image_format: str = "image/jpeg") -> ImageTags:
    tagger = ImageTagger()
    return await tagger.tag_image(image_data, image_format)

async def main():
    if len(sys.argv) != 2:
        print("Usage: python tag_image.py <path_to_image>")
        return

    image_path = sys.argv[1]
    
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        
        # Determine image format based on file extension
        image_format = f"image/{image_path.split('.')[-1].lower()}"
        
        tags = await tag_image(image_data, image_format)
        print(json.dumps(tags.__dict__, indent=2))
    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

