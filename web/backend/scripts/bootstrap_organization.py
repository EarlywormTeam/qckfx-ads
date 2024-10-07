import asyncio
import argparse
import base64
from toolbox.services.auth import AuthService
from toolbox.services.llm import LLMService
from toolbox.services.flags import FeatureFlags
from models.product import Product
from models.user import User
from scripts.strip_background_and_resize import strip_background_and_resize
from scripts.caption_image import caption_image

async def identify_product_in_image(llm_service, image_data):
    chat = llm_service.create_chat(
        system_prompt="""You are an AI assistant specialized in identifying products from images. 
        When shown an image, provide a concise, one to three-word description of the main product. 
        Focus on common retail items. Examples of appropriate responses include:
        "can", "pill bottle", "glass bottle", "macaron", "logo", "handbag", "blouse", "sneakers", "watch", "sunglasses", "backpack", "dress", "jacket", "necklace", "ring", "earrings", "wallet", "purse", "umbrella", "gloves", "sweater", "jeans", "skirt", "coat", "boots", "sandals", "bracelet".
        Always respond with a brief phrase that best describes the primary product in the image."""
    )

    encoded_image = base64.b64encode(image_data).decode('utf-8')
    image_content = chat.create_image_content(encoded_image)
    chat.create_user_message(
        chat.create_text_content("What is the main product in this image?"),
        image_content
    )

    detection_prompt = await chat.chat_completion(max_tokens=50)
    return detection_prompt.strip().lower()

async def bootstrap_organization(image_url: str, org_name: str, product_name: str, org_domain: str = None):
    # Initialize services
    auth_service = AuthService()
    llm_service = LLMService()

    try:
        # Find the user
        user = await User.find_one(User.email == "chris.wood@qckfx.com")
        if not user:
            raise Exception("User not found")

        # Strip background and resize image
        processed_image_name = f"{product_name.lower().replace(' ', '_')}.png"
        image_data, blob_url = await strip_background_and_resize(image_url, processed_image_name)
        
        if not blob_url or not image_data:
            raise Exception("Failed to process the image")

        # Caption the image
        image_caption = await caption_image(blob_url, llm_service)

        # Identify the object in the image
        detection_prompt = await identify_product_in_image(llm_service, image_data)

        # Create organization
        org_data = await auth_service.create_organization(org_name, org_domain)

        # Create product
        product = Product.create(
            name=product_name,
            organization_id=org_data['id'],
            created_by_user_id=user.id,  # Use the found user's ID
            primary_image_url=blob_url,
        )
        product.description = image_caption
        product.detection_prompt = detection_prompt
        product.stage = "completed"
        await product.save()

        print(f"Organization '{org_name}' and product '{product_name}' created successfully.")
        return org_data, product.model_dump()

    except Exception as e:
        print(f"Error in bootstrap_organization: {str(e)}")
        raise

async def main():
    parser = argparse.ArgumentParser(description="Bootstrap an organization and product.")
    parser.add_argument("image_url", help="URL of the product image")
    parser.add_argument("org_name", help="Name of the organization")
    parser.add_argument("product_name", help="Name of the product")
    parser.add_argument("--org_domain", help="Domain of the organization (optional)")

    args = parser.parse_args()

    try:
        org_data, product_data = await bootstrap_organization(
            image_url=args.image_url,
            org_name=args.org_name,
            product_name=args.product_name,
            org_domain=args.org_domain
        )
        print("Organization data:", org_data)
        print("Product data:", product_data)
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

