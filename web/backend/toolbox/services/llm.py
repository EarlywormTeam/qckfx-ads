import os

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from dotenv import load_dotenv

class LLMService:
    def __init__(self):
        load_dotenv()
        self.anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def create_chat(self, system_prompt, initial_messages=None, client="openai"):
        return Chat(self, client, system_prompt, initial_messages)

    async def create_embedding(self, text):
        return (await self.openai_client.embeddings.create(input=text, model="text-embedding-3-small")).data[0].embedding

    def create_image_content(self, image_base64, media_type="image/jpeg", client="openai"):
        if client == "openai":
            return {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{media_type};base64,{image_base64}",
                }
            }
        elif client == "anthropic":
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": image_base64,
                }
            }
        else:
            raise ValueError(f"Invalid client: {client}")

    def create_text_content(self, text, client="openai"):
        return {
            "type": "text",
            "text": text
        }

    def create_user_message(self, *content_pieces, client="openai"):
        return {
            "role": "user",
            "content": list(content_pieces)
        }

    def create_assistant_message(self, *content_pieces, client="openai"):
        return {
            "role": "assistant",
            "content": list(content_pieces)
        }

class Chat:
    def __init__(self, llm_service, client, system_prompt, initial_messages=None):
        self.llm_service = llm_service
        self.client = client
        self.system_prompt = system_prompt
        self.messages = []
        if initial_messages:
            self.messages.extend(initial_messages)

    async def chat_completion(self, model=None, pydantic_object=None, max_tokens=1000, temperature=0):
        try:
            if self.client == "anthropic":
                if not model:
                    model = "claude-3-5-sonnet-20240620"
                response = await self.llm_service.anthropic_client.messages.create(
                    model=model,
                    messages=self.messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=self.system_prompt
                )
                assistant_message = response.content[0].text
                self.messages.append({"role": "assistant", "content": assistant_message})
                return assistant_message
            elif self.client == "openai":
                if not model:
                    model = "gpt-4o"
                self.messages.insert(0, {"role": "system", "content": self.system_prompt})
                if pydantic_object:
                    response = await self.llm_service.openai_client.beta.chat.completions.parse(
                        model=model,
                        messages=self.messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        response_format=pydantic_object
                    )
                    assistant_message = response.choices[0].message.parsed
                    self.messages.append({"role": "assistant", "content": assistant_message.model_dump_json()}) 
                    return assistant_message
                else:
                    response = await self.llm_service.openai_client.chat.completions.create(
                        model=model,
                        messages=self.messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    assistant_message = response.choices[0].message.content
                    self.messages.append({"role": "assistant", "content": assistant_message})
                    return assistant_message
        except Exception as e:
            raise Exception(f"Error in chat completion: {str(e)}")

    def __getattr__(self, name):
        if name.startswith('create_'):
            method = getattr(self.llm_service, name)
            def wrapper(*args, **kwargs):
                result = method(*args, **kwargs, client=self.client)
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
