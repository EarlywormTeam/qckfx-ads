from beanie import Document, Indexed, PydanticObjectId
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class DeletionInfo(BaseModel):
    time: datetime
    user_id: str

class GeneratedImageGroup(Document):
    organization_id: Indexed(PydanticObjectId)
    product_id: Indexed(PydanticObjectId)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted: Optional[DeletionInfo] = Field(default=None)
    default_image_id: Optional[PydanticObjectId] = None

    class Settings:
        name = "generated_image_groups"
        use_state_management = True

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            PydanticObjectId: lambda v: str(v)
        }

    @classmethod
    async def create(cls, organization_id: PydanticObjectId, product_id: PydanticObjectId):
        return cls(
            organization_id=organization_id,
            product_id=product_id,
        )

    async def mark_as_deleted(self, user_id: str):
        self.deleted = DeletionInfo(
            time=datetime.utcnow(),
            user_id=user_id
        )
        await self.save()

    async def set_default_image(self, image_id: PydanticObjectId):
        self.default_image_id = image_id
        await self.save()
