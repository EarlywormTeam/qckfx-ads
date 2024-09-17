from beanie import PydanticObjectId
from models import GenerationJob, GeneratedImage, Product, ImageStatus
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
        image_generator = image_service.generate_images_stream(prompt, count, str(product_id), str(generation_job_id), product.lora_name, product.description, product.trigger_word, product.detection_prompt)

        print(image_generator, "image_generator")
        # Upload the generated image to blob storage
        blob_storage = toolbox.services.blob_storage

        failed_images = 0
        # Process each image as it's generated
        async for index, image_datum in image_generator:
            try:
                print(index, image_datum, "image_datum")
                # Create a new GeneratedImage document for each expected image
                generated_image = await GeneratedImage.create(
                    generation_job_id=generation_job.id,
                    group_id=image_group_ids[index],
                    status=ImageStatus.PENDING
                )
                await generated_image.save()

                if image_datum is None:
                    # Image generation failed
                    raise ValueError(f"Image {index + 1}/{count} generation failed")

                # Generate a unique blob name for each image
                blob_name = f"generated_image_{generation_job_id}_{index}.jpg"
                
                # Upload each image to blob storage
                blob_id = await blob_storage.upload_blob(blob_name, image_datum)

                # Get the URL of the uploaded image
                image_url = await blob_storage.get_blob_url(blob_id)

                # Update the generated image with the URL and status
                generated_image.url = image_url
                generated_image.status = ImageStatus.GENERATED
                await generated_image.save()

                # Update the generation job with progress
                await generation_job.add_log_entry(f"Image {index + 1}/{count} generated")

            except Exception as img_error:
                await generation_job.add_log_entry(f"Image {index + 1}/{count} generation failed")
                generated_image.status = ImageStatus.FAILED
                await generated_image.save()
                failed_images += 1
                continue

        # Update the generation job status based on overall results
        if failed_images == count:
            await generation_job.update_status('failed')
            await generation_job.add_log_entry("All images failed to generate")
        else:
            await generation_job.update_status('completed')
            await generation_job.add_log_entry(f"Image generation completed. {failed_images}/{count} images failed.")

    except Exception as e:
        # Update the generation job with error status and log the error
        if generation_job:
            await generation_job.update_status("error")
            await generation_job.add_log_entry(f"Error during image generation: {str(e)}")
        raise
