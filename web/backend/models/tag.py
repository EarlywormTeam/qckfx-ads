from beanie import Document, Link
from pydantic import Field

class Tag(Document):
    name: str = Field(..., description="Name of the tag")
    category: str = Field(..., description="Category of the tag (e.g., people, lighting, emotions, etc.)")
    organization: Link["Organization"] = Field(..., description="Reference to the organization the tag belongs to")

    class Settings:
        name = "tags"
        indexes = [
            "name",
            "category",
            "organization",
        ]

    class Config:
        schema_extra = {
            "example": {
                "name": "sunny",
                "category": "weather",
                "organization": "5f7b5e7a1c9d440000d5a3b1"
            }
        }

from .organization import Organization