from datetime import datetime
from typing import Optional
from beanie import Document, Link
from pydantic import Field

class Person(Document):
    name: Optional[str] = Field(None, description="Name of the person")
    representative_face: Link["Face"] = Field(..., description="Reference to the representative face of the person")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of person creation")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of last person update")

    class Settings:
        name = "persons"
        indexes = [
            "name",
            "representative_face",
            "created_at",
            "updated_at"
        ]

    class Config:
        schema_extra = {
            "example": {
                "name": "John Doe",
                "representative_face": "5f7b5e7a1c9d440000d5a3b1",
                "created_at": "2023-06-01T12:00:00Z",
                "updated_at": "2023-06-01T12:00:00Z"
            }
        }

from .face import Face

