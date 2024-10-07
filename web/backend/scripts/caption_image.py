import base64
from PIL import Image
from io import BytesIO
from toolbox.services.llm import LLMService

async def caption_image(file_path, llm_service, prefix="", postfix=""):
    # Open and encode the image
    with Image.open(file_path) as img:
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    # Create a chat instance
    chat = llm_service.create_chat(
        "You are an expert at describing images in painstaking detail. "
        "Your task is to analyze the given image and provide a description "
        "as though it were an image generation prompt. Be thorough and specific."
    )
    
    # Create the message with the image
    chat.create_user_message(
        chat.create_text_content("Please describe this image in painstaking detail, as if writing an image generation prompt:"),
        chat.create_image_content(img_base64, media_type="image/png")
    )
    
    # Get the chat completion
    response = await chat.chat_completion(max_tokens=1000)
    caption = response.strip()
    
    # Add spaces to prefix and postfix if needed
    prefix_with_space = prefix if prefix.endswith(' ') else prefix + ' '
    postfix_with_space = postfix if postfix.startswith(' ') else ' ' + postfix
    
    full_caption = f"{prefix_with_space}{caption}{postfix_with_space}".strip()
    
    return full_caption
