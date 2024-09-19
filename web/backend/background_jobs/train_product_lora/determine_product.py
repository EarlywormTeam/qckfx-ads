import base64

from toolbox import Toolbox
from models.product import Product

async def determine_product(toolbox: Toolbox, image_filename: str, product: Product):
    try:
        llm_service = toolbox.services.llm
        chat = llm_service.create_chat(
            system_prompt="""You are an AI assistant specialized in identifying products from images. 
            When shown an image, provide a concise, one-word description of the main product. 
            Focus on common retail items. Examples of appropriate responses include:
            "can", "bottle", "handbag", "blouse", "khakis", "sneakers", "watch", "sunglasses", "backpack", "dress", "jacket", "hat", "necklace", "ring", "earrings", "scarf", "tie", "belt", "wallet", "purse", "suitcase", "umbrella", "gloves", "socks", "sweater", "jeans", "shorts", "skirt", "coat", "boots", "sandals", "bracelet".
            Always respond with a single word that best describes the primary product in the image."""
        )

        # Read and encode the image to base64
        with open(image_filename, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Create the image content
        image_content = chat.create_image_content(encoded_image)

        # Create a user message with the image
        chat.create_user_message(
            chat.create_text_content("What is the main product in this image?"),
            image_content
        )

        # Get the response from the LLM
        response = await chat.chat_completion(max_tokens=50)

        description = response.strip().lower()
        
        # Update the product with the description
        await product.set_description(description)

        return description
    except Exception as e:
        error_message = f"Error in determine_product: {str(e)}"
        toolbox.logger.error(error_message)
        await product.set_stage("error")
        await product.add_log(error_message)
        raise
