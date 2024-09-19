import base64
import asyncio

async def generate_caption(toolbox, image_url: str, product_description: str, trigger_word: str) -> str:
    llm_service = toolbox.services.llm
    blob_storage = toolbox.services.blob_storage

    system_prompt = f"""You are an AI assistant specialized in generating captions for product images. 
    The product is described as: "{product_description}".
    Generate a brief caption that describes the scene in the image while mentioning the product.
    
    Examples for a product described as "Calm Crunchy sparkling water":
    1. "A couple on a beach. The woman is holding a Calm Crunchy sparkling water can."
    2. "Cans lined up on a cloth. The blue can in the center is a can of Calm Crunchy sparkling water."
    3. "A family outside. The mother is holding a can of Calm Crunchy sparkling water."
    
    Provide a similar style of caption for the given image and product."""

    chat = llm_service.create_chat(system_prompt)

    # Download and encode the image
    image_data = await blob_storage.download_blob(image_url)
    encoded_image = base64.b64encode(image_data).decode('utf-8')

    # Create the image content
    image_content = chat.create_image_content(encoded_image)

    # Create a user message with the image
    chat.create_user_message(
        chat.create_text_content("Please provide a caption for this image."),
        image_content
    )

    # Get the response from the LLM
    response = await chat.chat_completion(max_tokens=500)

    # Preface the caption with "a photo of {product_description}"
    prefaced_caption = f"a photo of {trigger_word}: {response.strip()}"

    return prefaced_caption

async def generate_captions(toolbox, image_urls: list[str], product_description: str, trigger_word: str) -> list[str]:
    caption_tasks = [generate_caption(toolbox, url, product_description, trigger_word) for url in image_urls]
    captions = await asyncio.gather(*caption_tasks)
    return captions
