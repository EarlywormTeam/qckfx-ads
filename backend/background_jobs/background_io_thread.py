import threading
import asyncio

from models import init_beanie_models
from toolbox import Toolbox

class BackgroundIOThread:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()
        self.toolbox = Toolbox()

    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._init_runloop())
        self.loop.run_forever()

    async def _init_runloop(self):
       await init_beanie_models()

    async def run_async_task(self, func, *args, **kwargs):
        coro = func(self.toolbox, *args, **kwargs)
        return await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(coro, self.loop))

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()


background_io_thread = BackgroundIOThread()

# The task is carried out in the background thread in an async manner
async def run_async_task(func, *args, **kwargs):
    return await background_io_thread.run_async_task(func, *args, **kwargs)

# The task is carried out in the background in a blocking manner (throws exceptions)
def run_task(func, *args, **kwargs):
    async def wrapper():
        return await background_io_thread.run_async_task(func, *args, **kwargs)

    future = asyncio.run_coroutine_threadsafe(wrapper(), background_io_thread.loop)
    try:
        return future.result()
    except Exception as e:
        raise e

# Usage example:
# background_io = BackgroundIOThread()
# 
# async def some_async_task(toolbox: Toolbox, param1: str, param2: str) -> str:
#     claude_client = toolbox.services.claude
#     # Use claude_client and other toolbox objects as needed
#     await asyncio.sleep(1)
#     return f"Task completed with {param1} and {param2}"
# 
# result = await background_io.run_with_toolbox(some_async_task, "arg1", "arg2")
# print(result)
# 
# background_io.stop()