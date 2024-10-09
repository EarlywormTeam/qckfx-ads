from beanie import PydanticObjectId
import numpy as np
from typing import List
from io import BytesIO
from PIL import Image
from pydantic import BaseModel, Field
import matplotlib.pyplot as plt
import asyncio
import requests
import base64
from urllib.parse import urlparse
import os

from models.product import Product
from toolbox.services.llm import LLMService

class ProductDetectionDetails(BaseModel):
    detections: List[Product] = Field(default_factory=list)

class ProductExtractor:
    def __init__(self):
        # Initialize LLM Service
        self.llm_service = LLMService()

    def load_image(self, image_data: bytes) -> np.ndarray:
        image = Image.open(BytesIO(image_data)).convert('RGB')
        return np.array(image)

    async def check_product_in_image(self, product: Product, image_data: bytes, image_format: str = "jpeg") -> bool:
        # Fetch product image
        try:
            product_image_response = requests.get(product.primary_image_url)
            product_image_response.raise_for_status()
            product_image_data = product_image_response.content
        except requests.RequestException as e:
            print(f"Error fetching product image for {product.name}: {e}")
            return False

        # Extract file extension from product image URL
        product_image_ext = os.path.splitext(urlparse(product.primary_image_url).path)[1][1:]
        if not product_image_ext:
            product_image_ext = "png"  # Default to png if no extension found

        # Create chat with LLM
        chat = self.llm_service.create_chat(
            system_prompt="You are an image analysis assistant."
        )

        product_image_base64 = base64.b64encode(product_image_data).decode('utf-8')
        image_data_base64 = base64.b64encode(image_data).decode('utf-8')
        chat.messages.append(self.llm_service.create_user_message(
            self.llm_service.create_image_content(product_image_base64, f"image/{product_image_ext}"),
            self.llm_service.create_image_content(image_data_base64, f"image/{image_format}"),
            self.llm_service.create_text_content(
                "Does the first image depict a product shown in the second image? Be as accurate as possible, answer yes only if you are absolutely sure. Prefer to be conservative and answer no if you are not sure. Emphasize precision over recall. Answer with only a 'yes' or 'no'."
            )
        ))
        response = await chat.chat_completion()
        response_clean = response.strip().lower()
        print(f"LLM response for {product.name}: {response_clean}")
        return 'yes' in response_clean

    async def extract_products(self, image_data: bytes, products: List[Product], image_format: str = "jpeg") -> ProductDetectionDetails:
        # Create a list of coroutines for each product check
        check_coroutines = [self.check_product_in_image(product, image_data, image_format) for product in products]
        
        # Await all coroutines concurrently
        results = await asyncio.gather(*check_coroutines)
        
        # Create a list of detected products based on the results
        detected_products = [product for product, is_present in zip(products, results) if is_present]
        
        return ProductDetectionDetails(detections=detected_products)

def display_product_detections(image_data: bytes, detections: ProductDetectionDetails):
    image = Image.open(BytesIO(image_data)).convert('RGB')
    plt.figure(figsize=(12, 8))
    plt.imshow(image)
    ax = plt.gca()

    # Display detected products as a list on the image
    detected_names = [f"Detected Product: {product.name}" for product in detections.detections]
    display_text = "\n".join(detected_names)
    if detected_names:
        plt.text(10, 10, display_text, fontsize=12, color='green', backgroundcolor='white', verticalalignment='top')
    else:
        plt.text(10, 10, "No products detected.", fontsize=12, color='red', backgroundcolor='white', verticalalignment='top')

    plt.axis('off')
    plt.show()

async def main():
    import sys
    from models import init_beanie_models

    await init_beanie_models()

    if len(sys.argv) < 3:
        print("Usage: python extract_products.py <image_path> <product_ids_comma_separated>")
        sys.exit(1)

    image_path = sys.argv[1]
    product_ids = sys.argv[2].split(',')

    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{image_path}' was not found.")
        sys.exit(1)
    except IOError:
        print(f"Error: Unable to read the file '{image_path}'.")
        sys.exit(1)

    # Fetch products from the database (assuming asynchronous ORM)
    products = []
    for pid in product_ids:
        product = await Product.get(PydanticObjectId(pid))
        if product:
            products.append(product)
        else:
            print(f"Product with ID {pid} not found.")

    extractor = ProductExtractor()
    detection_details = await extractor.extract_products(image_data, products)

    # Display the results
    display_product_detections(image_data, detection_details)

    # Print detected products
    for product in detection_details.detections:
        print(f"Detected Product: {product.name}")

if __name__ == "__main__":
    asyncio.run(main())
