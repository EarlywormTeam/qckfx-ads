import os
import asyncio
from asyncio import Queue, Semaphore
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from functools import wraps

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from dotenv import load_dotenv

class ChatCompletionQueue:
    _instance = None

    def __new__(cls, llm_service, rate_limit=5, max_failures=5):
        if cls._instance is None:
            cls._instance = super(ChatCompletionQueue, cls).__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self, llm_service, rate_limit=5, max_failures=5):
        if self.__initialized:
            return
        self.__initialized = True
        self.llm_service = llm_service
        self.rate_limit = rate_limit  # Max concurrent requests per second
        self.max_failures = max_failures
        self.queue = Queue()
        self.failure_count = 0
        self.lock = asyncio.Lock()
        self.semaphore = Semaphore(rate_limit)
        asyncio.create_task(self.run())

    async def enqueue(self, request):
        await self.queue.put(request)

    async def run(self):
        while True:
            batch = []
            # Collect up to `rate_limit` requests
            for _ in range(self.rate_limit):
                if self.queue.empty():
                    break
                request = await self.queue.get()
                batch.append(request)

            if not batch:
                await asyncio.sleep(0.1)  # Small sleep to prevent tight loop
                continue

            # Process the batch concurrently
            tasks = []
            for request in batch:
                task = asyncio.create_task(self.process_request(request))
                tasks.append(task)

            # Wait for all tasks in the batch to complete
            # await asyncio.gather(*tasks)

            # Wait for 1/10 second before processing the next batch
            await asyncio.sleep(0.1)

    async def process_request(self, request):
        chat_instance, model, pydantic_object, max_tokens, temperature, future = request
        try:
            # Acquire semaphore to respect rate limiting
            async with self.semaphore:
                response = await chat_instance._original_chat_completion(
                    model, pydantic_object, max_tokens, temperature
                )
                future.set_result(response)
            async with self.lock:
                self.failure_count = 0  # Reset on success
        except Exception as e:
            async with self.lock:
                self.failure_count += 1
                if self.failure_count >= self.max_failures:
                    future.set_exception(Exception("Max consecutive failures reached. Stopping queue processing."))
                    self.failure_count = 0  # Reset after reaching max to prevent indefinite blocking
                else:
                    # Re-queue the request for retry
                    await self.queue.put(request)

class LLMService:
    def __init__(self):
        load_dotenv()
        self.anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.chat_completion_queue = ChatCompletionQueue(self)

    def create_chat(self, system_prompt, initial_messages=None, client="openai"):
        return Chat(self, client, system_prompt, initial_messages)

    def enqueue_chat_completion(self, chat_instance, model, pydantic_object, max_tokens, temperature):
        return self.chat_completion_queue.enqueue((chat_instance, model, pydantic_object, max_tokens, temperature, asyncio.get_event_loop().create_future()))

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

    def create_text_content(self, text, client="penai"):
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
        # Preserve the original chat_completion method
        self._original_chat_completion = self.chat_completion
        # Replace chat_completion with the decorated version
        self.chat_completion = self._queue_decorator(self._original_chat_completion)

    def _queue_decorator(self, func):
        @wraps(func)
        async def wrapper(model=None, pydantic_object=None, max_tokens=1000, temperature=0):
            loop = asyncio.get_event_loop()
            future = loop.create_future()
            # Enqueue the request
            await self.llm_service.chat_completion_queue.enqueue(
                (self, model, pydantic_object, max_tokens, temperature, future)
            )
            # Await the result
            return await future
        return wrapper

    @retry(
        retry=retry_if_exception_type((asyncio.TimeoutError, ConnectionError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
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
        except (asyncio.TimeoutError, ConnectionError) as e:
            # Log the error or handle it as needed
            print(f"Connection error occurred: {str(e)}. Retrying...")
            raise  # Re-raise the exception to trigger the retry
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