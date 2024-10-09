from datetime import datetime
from typing import List, Optional
from beanie import Document, BackLink, Link
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    x: float = Field(..., description="X-coordinate of the top-left corner")
    y: float = Field(..., description="Y-coordinate of the top-left corner")
    width: float = Field(..., description="Width of the bounding box")
    height: float = Field(..., description="Height of the bounding box")

class Face(Document):
    image: Optional[BackLink["Image"]] = Field(None, description="Reference to the image containing this face", original_field="faces")
    file_path: str = Field(..., description="Path to the aligned face image file")
    phash: str = Field(..., description="Perceptual hash of the face")
    organization: Link["Organization"] = Field(..., description="Reference to the organization the face belongs to")
    face_embedding: List[float] = Field(..., description="Vector representation of the face")
    bounding_box: BoundingBox = Field(..., description="Coordinates of the face within the image")
    detection_confidence: float = Field(..., description="Confidence of the face detection model")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of face detection")
    person: Optional[Link["Person"]] = Field(None, description="Reference to the person the face belongs to")
    class Settings:
        name = "faces"
        indexes = [
            "created_at",
            "organization",
            "image",
            "person",
            "phash"
        ]

    class Config:
        schema_extra = {
            "example": {
                "image": "5f7b5e7a1c9d440000d5a3b1",
                "file_path": "path/to/image/file.jpg",
                "organization": "5f7b5e7a1c9d440000d5a3b1",
                "face_embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
                "bounding_box": {
                    "x": 100.0,
                    "y": 150.0,
                    "width": 200.0,
                    "height": 250.0
                },
                "detection_confidence": 0.95,
                "created_at": "2023-06-01T12:00:00Z",
                "person": "5f7b5e7a1c9d440000d5a3b1"
            }
        }

from .image import Image
from .organization import Organization
from .person import Person
