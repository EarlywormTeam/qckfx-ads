import asyncio

from beanie import PydanticObjectId
from toolbox import Toolbox
from .index_image import background_process_uploaded_image

async def index_uploaded_images(toolbox: Toolbox, organization_id: PydanticObjectId, user_id: PydanticObjectId, image_filepaths: list[str]):
    print(f"Indexing {len(image_filepaths)} images for organization {organization_id}")
    async def process_image(filepath: str):
        try:
            await background_process_uploaded_image(
                toolbox,
                creation_method="upload",
                user_id=user_id,
                organization_id=organization_id,
                blob_path=filepath
            )
        except Exception as e:
            print(f"Error processing image {filepath}: {str(e)}")

    # Create tasks for each image filepath
    tasks = [process_image(filepath) for filepath in image_filepaths]

    # Run all tasks concurrently
    await asyncio.gather(*tasks)

    print(f"Finished indexing {len(image_filepaths)} images for organization {organization_id}")
