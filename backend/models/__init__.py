from .generation_job import GenerationJob
from .generated_image import GeneratedImage
from .generated_image_group import GeneratedImageGroup
from .organization import Organization, OrganizationMembership
from .product import Product
from .user import User

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

async def init_beanie_models():
    # Load environment variables
    load_dotenv()
    
    # Get connection string from environment
    connection_string = os.getenv("MONGODB_URL")
    
    # Create Motor client
    client = AsyncIOMotorClient(connection_string)
    
    # Initialize Beanie with all the models
    await init_beanie(
        database=client.qckfx,
        document_models=[
            GenerationJob,
            GeneratedImage,
            GeneratedImageGroup,
            Organization,
            OrganizationMembership,
            Product,
            User
        ],
        multiprocessing_mode=True
    )
