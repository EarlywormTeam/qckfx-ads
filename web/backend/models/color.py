from beanie import Document, Link
from pydantic import Field
from typing import List

class Color(Document):
    lab_vector: List[float] = Field(..., description="LAB color vector [L, A, B]")
    organization: Link["Organization"] = Field(..., description="Reference to the organization the color belongs to")

    class Settings:
        name = "colors"
        indexes = [
            "lab_vector",
            "organization",
        ]

    class Config:
        schema_extra = {
            "example": {
                "lab_vector": [50.0, -20.0, 30.0],
                "organization": "5f7b5e7a1c9d440000d5a3b1"
            }
        }

from .organization import Organization