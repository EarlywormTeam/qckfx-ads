import os

from anthropic import AsyncAnthropic
from dotenv import load_dotenv

class LLMService:
    def __init__(self):
        load_dotenv()
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def create_chat(self, system_prompt, initial_messages=None):
        return Chat(self, system_prompt, initial_messages)

    def create_image_content(self, image_base64, media_type="image/jpeg"):
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": image_base64,
            }
        }

    def create_text_content(self, text):
        return {
            "type": "text",
            "text": text
        }

    def create_user_message(self, *content_pieces):
        return {
            "role": "user",
            "content": list(content_pieces)
        }

    def create_assistant_message(self, *content_pieces):
        return {
            "role": "assistant",
            "content": list(content_pieces)
        }

class Chat:
    def __init__(self, llm_service, system_prompt, initial_messages=None):
        self.llm_service = llm_service
        self.system_prompt = system_prompt
        self.messages = []
        if initial_messages:
            self.messages.extend(initial_messages)

    async def chat_completion(self, model="claude-3-5-sonnet-20240620", max_tokens=1000, temperature=0):
        try:
            response = await self.llm_service.client.messages.create(
                model=model,
                messages=self.messages,
                max_tokens=max_tokens,
                temperature=temperature,
                system=self.system_prompt
            )
            assistant_message = response.content[0].text
            self.messages.append({"role": "assistant", "content": assistant_message})
            return assistant_message
        except Exception as e:
            raise Exception(f"Error in chat completion: {str(e)}")

    def __getattr__(self, name):
        if name.startswith('create_'):
            method = getattr(self.llm_service, name)
            def wrapper(*args, **kwargs):
                result = method(*args, **kwargs)
                if name in ['create_user_message', 'create_assistant_message']:
                    self.messages.append(result)
                return result
            return wrapper
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

# Usage example:
# llm_service = LLMService()
# chat = llm_service.create_chat("You are a helpful assistant.")
# chat.create_user_message("What's the capital of France?")
# response = await chat.chat_completion()
# print(response)
