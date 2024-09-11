from beanie import PydanticObjectId
from models import GenerationJob, GeneratedImage, GeneratedImageGroup, ImageStatus
from toolbox import Toolbox

async def background_refine_product_image(toolbox: Toolbox, image_group_id: PydanticObjectId, image_id: PydanticObjectId, prompt: str, generation_job_id: PydanticObjectId):
    refined_image = None
    try:
        # Get the generation job and image group from the database
        generation_job = await GenerationJob.get(generation_job_id)
        image_group = await GeneratedImageGroup.get(image_group_id)

        if not generation_job or not image_group:
            raise ValueError("Generation job or image group not found")

        # Update the generation job status and logs
        await generation_job.update_status("in_progress")
        await generation_job.add_log_entry("Starting image refinement")

        # Get the original image to refine
        original_image = await GeneratedImage.find_one(GeneratedImage.id == image_id)
        if not original_image:
            raise ValueError("Original image not found")

        # Download the original image
        blob_storage = toolbox.services.blob_storage
        # Get the blob name from the last part of the URL path and remove the extension
        blob_name = original_image.url.split('/')[-1]
        original_image_data = await blob_storage.download_blob(blob_name)

        # Create a new GeneratedImage document for the refined image with PENDING status
        refined_image = await GeneratedImage.create(
            generation_job_id=generation_job.id,
            group_id=image_group.id,
            status=ImageStatus.PENDING
        )
        await refined_image.save()

        # Refine the image using the image service
        image_service = toolbox.services.image_service
        refined_image_data = await image_service.refine_image(
            original_image_data, 
            prompt, 
            str(generation_job_id)
        )

        # Upload the refined image to blob storage
        blob_name = f"refined_image_{generation_job_id}.jpg"
        blob_id = await blob_storage.upload_blob(blob_name, refined_image_data[0])  # Assuming refine_image returns a list with one item
        image_url = await blob_storage.get_blob_url(blob_id)

        # Update the refined image with the URL and status
        refined_image.url = image_url
        refined_image.status = ImageStatus.GENERATED
        await refined_image.save()

        # Update the generation job with completed status
        await generation_job.update_status('completed')
        await generation_job.add_log_entry("Image refinement completed successfully")

    except Exception as e:
        # Update the generation job with error status and log the error
        if generation_job:
            await generation_job.update_status("error")
            await generation_job.add_log_entry(f"Error during image refinement: {str(e)}")
        
        # Delete the failed refined image if it was created
        if refined_image:
            await refined_image.delete()

        raise



