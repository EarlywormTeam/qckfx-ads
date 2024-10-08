from models.product import Product
from toolbox import Toolbox
from toolbox.services.blob_storage import BlobStorageService

async def remove_background(toolbox: Toolbox, product: Product) -> str:
    blob_service = toolbox.services.blob_storage
    try:
        # Use the stored image URL directly
        image_url = product.primary_image_url

        # Use the image service to remove the background
        image_service = toolbox.services.image_service
        result_url = await image_service.remove_background(image_url)

        # Upload the background-removed image to blob storage
        blob_name = f"background_removed_{product.id}.png"
        new_blob_id = await blob_service.upload_blob_from_url(blob_name, result_url, BlobStorageService.ContainerName.IMAGES)

        # Update the product with the new background-removed image blob ID and URL
        new_blob_url = await blob_service.get_blob_url(new_blob_id, BlobStorageService.ContainerName.IMAGES)
        await product.set_background_removed_image(new_blob_id, new_blob_url)

        return new_blob_id
    except Exception as e:
        toolbox.services.logger.error(f"Error removing background for product {product.id}: {str(e)}")
        # Update product stage to error if necessary
        await product.update_stage("error")
        await product.add_log_entry(f"Error removing background: {str(e)}")
        raise

