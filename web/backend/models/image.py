from datetime import datetime
from typing import List, Optional
from beanie import Document, Link
from pydantic import BaseModel, Field

class DominantColor(BaseModel):
    vector: List[float] = Field(..., description="Lab values of the dominant color")
    percentage: float = Field(..., description="Percentage of the image this color occupies")

class Dimensions(BaseModel):
    width: int = Field(..., description="Width of the image in pixels")
    height: int = Field(..., description="Height of the image in pixels")
    aspect_ratio: float = Field(..., description="Aspect ratio of the image")

class Image(Document):
    organization: Link["Organization"] = Field(..., description="Reference to the organization the image belongs to")
    created_by_user: Link["User"] = Field(..., description="Reference to the user who created the image")
    creation_method: str = Field(..., description="Method used to create the image (generated or uploaded)")
    file_path: str = Field(..., description="Path to the image file")
    phash: str = Field(..., description="Perceptual hash of the image")
    dimensions: Dimensions = Field(..., description="Dimensions of the image")
    resolution: int = Field(..., description="Resolution of the image in DPI")
    format: str = Field(..., description="File format of the image")
    dominant_colors: List[DominantColor] = Field(default_factory=list, description="List of dominant colors in the image")
    detected_products: List[Link["Product"]] = Field(default_factory=list, description="List of detected product IDs in the image")
    caption: Optional[str] = Field(None, description="Caption describing the image")
    caption_embedding: Optional[List[float]] = Field(None, description="Vector embedding of the image caption")
    tags: List[Link["Tag"]] = Field(default_factory=list, description="List of tags associated with the image")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of image creation")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of last image update")
    faces: List[Link["Face"]] = Field(default_factory=list, description="References to faces detected in the image")

    class Settings:
        name = "images"
        indexes = [
            "faces",
            "detected_products",
            "organization",
            "created_by_user",
            "tags",
            "created_at",
            "updated_at",
            "creation_method",
            "phash"
        ]

    class Config:
        schema_extra = {
            "example": {
                "file_path": "/path/to/image.jpg",
                "organization": "5f7b5e7a1c9d440000d5a3b1",
                "created_by_user": "5f7b5e7a1c9d440000d5a3b1",
                "creation_method": "uploaded",  
                "dimensions": {
                    "width": 1920,
                    "height": 1080,
                    "aspect_ratio": 1.78
                },
                "resolution": 300,
                "format": "JPEG",
                "dominant_colors": [
                    {"vector": [255, 0, 0], "percentage": 0.3},
                    {"vector": [0, 255, 0], "percentage": 0.2}
                ],
                "detected_products": ["product1", "product2"],
                "caption": "A beautiful sunset over the ocean",
                "caption_embedding": [0.1, 0.2, 0.3, 0.4],
                "tags": ["5f7b5e7a1c9d440000d5a3b1", "5f7b5e7a1c9d440000d5a3b2"],
                "created_at": "2023-06-01T12:00:00Z",
                "updated_at": "2023-06-01T12:00:00Z",
                "faces": ["5f7b5e7a1c9d440000d5a3b1", "5f7b5e7a1c9d440000d5a3b2"]
            }
        }

from .face import Face
from .organization import Organization
from .product import Product
from .user import User
from .tag import Tag