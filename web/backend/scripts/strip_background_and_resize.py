import asyncio
from io import BytesIO
from PIL import Image
from toolbox.services.image import ImageService
from toolbox.services.blob_storage import BlobStorageService, ContainerName
from toolbox.services.flags import FeatureFlags

def get_resampling_filter():
    if hasattr(Image, 'Resampling'):
        return Image.Resampling.LANCZOS
    else:
        return Image.LANCZOS

def resize_original(im, target_size=(768, 768)):
    """
    Resize image to fit within a 768x768 box while maintaining aspect ratio.
    """
    im.thumbnail(target_size, get_resampling_filter())
    new_im = Image.new("RGBA", target_size, (0,0,0,0))
    x_offset = (target_size[0] - im.width) // 2
    y_offset = (target_size[1] - im.height) // 2
    new_im.paste(im, (x_offset, y_offset))
    return new_im

async def strip_background_and_resize(image_url: str, filename: str):
    # Initialize services
    flags = FeatureFlags()  # Assuming you have a way to initialize FeatureFlags
    image_service = ImageService(flags)
    blob_storage_service = BlobStorageService()

    try:
        # Remove background
        output = await image_service.remove_background(image_url)
        
        if not output:
            raise Exception("Background removal failed")

        # Download the processed image
        image_data = await image_service.download_image(output)

        # Open the image with PIL
        with Image.open(BytesIO(image_data)) as im:
            # Resize the image
            resized_im = resize_original(im)

            # Save the resized image to a BytesIO object
            buffer = BytesIO()
            resized_im.save(buffer, format="PNG")
            buffer.seek(0)

        # Upload the processed and resized image to blob storage
        blob_name = await blob_storage_service.upload_blob(filename, buffer.getvalue(), ContainerName.IMAGES)
        
        # Get the blob URL
        blob_url = await blob_storage_service.get_blob_url(blob_name, ContainerName.IMAGES)
        
        return buffer.getvalue(), blob_url
    except Exception as e:
        print(f"Error in strip_background_and_resize: {str(e)}")
        return None, None

# Usage example:
# asyncio.run(strip_background_and_resize("https://example.com/image.jpg", "processed_image.png"))

