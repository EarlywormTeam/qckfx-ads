import asyncio
from toolbox import Toolbox
from models.product import Product
from .background_removal import remove_background
from .determine_product import determine_product
from .fine_tune_product import fine_tune_product

async def train_product_lora(toolbox: Toolbox, product: Product):
    try:
        # Run background removal and product determination concurrently
        background_task = asyncio.create_task(remove_background(toolbox, product))
        determine_task = asyncio.create_task(determine_product(toolbox, product.primary_image_url, product))

        # Wait for both tasks to complete
        await asyncio.gather(background_task, determine_task)

        # Run fine-tuning
        await fine_tune_product(toolbox, product)

        toolbox.logger.info(f"Product {product.id} training completed successfully.")
    except Exception as e:
        toolbox.logger.error(f"Error in train_product_lora: {str(e)}")
        if product:
            await product.update_stage("error")
            await product.add_log_entry(f"Error during training: {str(e)}")
