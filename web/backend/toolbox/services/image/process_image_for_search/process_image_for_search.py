import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List
from beanie import PydanticObjectId
from pydantic import BaseModel

from .extract_basic_details import extract_basic_details, ImageDetails
from .extract_dominant_colors import extract_dominant_colors, LABColor
from .extract_faces import extract_facial_details, FacialDetails
from .extract_products import ProductExtractor, ProductDetectionDetails
from .caption_image import caption_image
from .tag_image import tag_image, ImageTags
from models.product import Product
from models.image import DominantColor, Image

class ImageSearchMetadata(BaseModel):
    basic_details: ImageDetails
    dominant_colors: List[DominantColor]
    facial_details: FacialDetails
    product_details: ProductDetectionDetails
    image_caption: str
    image_tags: ImageTags

class ImageAlreadyExistsError(Exception):
    def __init__(self, phash: str, message: str = "An image with the same perceptual hash already exists for this organization."):
        self.phash = phash
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message} (phash: {self.phash})'


class BackgroundThreadQueue:
    def __init__(self):
        max_workers = 4
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
      
    async def submit(self, func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args, **kwargs)
    
background_thread_queue = BackgroundThreadQueue()
    
async def process_image_for_search(image_data: bytes, organization_id: PydanticObjectId) -> ImageSearchMetadata:
    # Extract basic details
    basic_details = extract_basic_details(image_data)

    # Check if an image with the same phash already exists for this organization
    existing_image = await Image.find_one({
        "organization.$id": organization_id,
        "phash": basic_details.phash
    })

    if existing_image:
        raise ImageAlreadyExistsError(basic_details.phash)

    # Get image format for caption and tag functions
    image_format = basic_details.file_type.lower()

    # Extract dominant colors
    dominant_colors_task = background_thread_queue.submit(extract_dominant_colors, image_data)

    # Extract facial details
    facial_details_task = background_thread_queue.submit(extract_facial_details, image_data)

    # Extract products, caption image, and tag image concurrently
    products = await Product.find(Product.organization_id == organization_id).to_list()
    product_extractor = ProductExtractor()
    
    product_details_task = product_extractor.extract_products(image_data, products, image_format)
    image_caption_task = caption_image(image_data, f"image/{image_format}")
    image_tags_task = tag_image(image_data, f"image/{image_format}")
    
    product_details, image_caption, image_tags, dominant_colors, facial_details = await asyncio.gather(
        product_details_task,
        image_caption_task,
        image_tags_task,
        dominant_colors_task,
        facial_details_task
    )

    # Compile all results
    results = ImageSearchMetadata(
        basic_details=basic_details,
        dominant_colors=dominant_colors,
        facial_details=facial_details,
        product_details=product_details,
        image_caption=image_caption,
        image_tags=image_tags
    )

    return results

# Example usage
async def main():
    # This is just for demonstration purposes
    image_path = "path/to/your/image.jpg"
    organization_id = PydanticObjectId("your_organization_id_here")

    with open(image_path, "rb") as f:
        image_data = f.read()

    results = await process_image_for_search(image_data, organization_id)
    print(results)

if __name__ == "__main__":
    asyncio.run(main())

