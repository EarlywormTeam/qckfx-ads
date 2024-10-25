from .color import Color
from .face import Face
from .generation_job import GenerationJob
from .generated_image import GeneratedImage, ImageStatus
from .generated_image_group import GeneratedImageGroup
from .image import Image
from .organization import Organization, OrganizationMembership
from .person import Person
from .product import Product
from .tag import Tag
from .user import User
from .waitlist import WaitlistEntry

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
            Color,
            Face,
            GenerationJob,
            GeneratedImage,
            GeneratedImageGroup,
            Image,
            Organization,
            OrganizationMembership,
            Person,
            Product,
            Tag,
            User,
            WaitlistEntry
        ],
        multiprocessing_mode=True
    )
