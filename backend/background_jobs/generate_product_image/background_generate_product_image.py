from beanie import PydanticObjectId
from models import GenerationJob, GeneratedImage, Product
from toolbox import Toolbox

async def background_generate_product_image(toolbox: Toolbox, prompt: str, count: int, product_id: PydanticObjectId, generation_job_id: PydanticObjectId, image_group_ids: [PydanticObjectId]):
    try:
        # Get the generation job, product, and image group from the database
        generation_job = await GenerationJob.get(generation_job_id)
        product = await Product.get(product_id)

        if not generation_job or not product_id or not image_group_ids:
            raise ValueError("Generation job, product, or image group not found")

        # Update the generation job status and logs
        await generation_job.update_status("in_progress")
        await generation_job.add_log_entry("Starting image generation")

        # Generate the image using the image service
        image_service = toolbox.services.image_service
        image_data = await image_service.generate_images(prompt, count, str(product_id), str(generation_job_id), product.lora_name, product.description, product.trigger_word, product.detection_prompt)

        # Upload the generated image to blob storage
        blob_storage = toolbox.services.blob_storage
        # Process each image datum in the list
        for index, image_datum in enumerate(image_data):
            # Generate a unique blob name for each image
            blob_name = f"generated_image_{generation_job_id}_{index}.jpg"
            
            # Upload each image to blob storage
            blob_id = await blob_storage.upload_blob(blob_name, image_datum)

            # Get the URL of the uploaded image
            image_url = await blob_storage.get_blob_url(blob_id)

            # Create a new GeneratedImage document and store the URL for each image
            generated_image = await GeneratedImage.create(
                generation_job_id=generation_job.id,
                group_id=image_group_ids[index],
                url=image_url
            )
            await generated_image.save()

        # Update the generation job with completed status
        await generation_job.update_status('completed')
        await generation_job.add_log_entry("Image generation completed successfully")

    except Exception as e:
        # Update the generation job with error status and log the error
        if generation_job:
            await generation_job.update_status("error")
            await generation_job.add_log_entry(f"Error during image generation: {str(e)}")
        raise
