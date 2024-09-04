from beanie import Document, Indexed, PydanticObjectId
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class DeletionInfo(BaseModel):
    time: datetime
    user_id: str

class GeneratedImage(Document):
    generation_job_id: Indexed(PydanticObjectId)
    url: str
    deleted: Optional[DeletionInfo] = Field(default=None)

    class Settings:
        name = "generated_images"
        use_state_management = True

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            PydanticObjectId: lambda v: str(v)
        }

    @classmethod
    async def create(cls, generation_job_id: PydanticObjectId, url: str):
        return cls(
            generation_job_id=generation_job_id,
            url=url
        )

    async def mark_as_deleted(self, user_id: str):
        self.deleted = DeletionInfo(
            time=datetime.utcnow(),
            user_id=user_id
        )
        await self.save()

