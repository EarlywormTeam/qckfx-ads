import zipfile
import tempfile
import os
from toolbox import Toolbox
from models.product import Product
from background_jobs.train_product_lora.generate_image_captions import generate_captions

async def fine_tune_product(toolbox: Toolbox, product: Product):
    image_service = toolbox.services.image_service
    blob_storage = toolbox.services.blob_storage

    # Prepare images and captions
    image_urls = [product.primary_image_url] + product.additional_image_urls
    captions = await generate_captions(toolbox, image_urls, product.description, product.trigger_word)

    # Create a temporary zip file with images and captions
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
        with zipfile.ZipFile(temp_zip, 'w') as zf:
            for i, (image_url, caption) in enumerate(zip(image_urls, captions)):
                image_data = await blob_storage.download_blob(image_url)
                zf.writestr(f"image_{i}.jpg", image_data)
                zf.writestr(f"image_{i}.txt", caption)

    # Upload the zip file to blob storage
    zip_blob_name = f"temp_zip_{product.id}.zip"
    zip_blob_id = await blob_storage.upload_blob(zip_blob_name, temp_zip.name)

    try:
        # Run fine-tuning
        result = await image_service.finetune_model(
            images_data_url=await blob_storage.get_blob_url(zip_blob_id),
            trigger_word=product.trigger_word
        )

        # Download and store LoRA weights
        lora_weights_url = result["diffusers_lora_file"]
        lora_weights_blob_id = await blob_storage.upload_blob_from_url(f"lora_{product.id}.safetensors", lora_weights_url)

        # Update product with LoRA weights blob ID and URL
        lora_weights_blob_url = await blob_storage.get_blob_url(lora_weights_blob_id)
        await product.set_lora_weights(lora_weights_blob_id, lora_weights_blob_url)
        await product.update_stage("completed")
        await product.add_log_entry("Fine-tuning completed successfully")

    except Exception as e:
        await product.update_stage("error")
        await product.add_log_entry(f"Error during fine-tuning: {str(e)}")
        raise

    finally:
        # Clean up temporary zip file
        os.unlink(temp_zip.name)

        # Delete the temporary zip file from blob storage
        await blob_storage.delete_blob(zip_blob_id)