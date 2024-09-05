from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field
from datetime import datetime

class GeneratedImage(Document):
    generation_job_id: Indexed(PydanticObjectId)
    group_id: Indexed(PydanticObjectId)
    url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "generated_images"
        use_state_management = True

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            PydanticObjectId: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }

    @classmethod
    async def create(cls, generation_job_id: PydanticObjectId, group_id: PydanticObjectId, url: str):
        return cls(
            generation_job_id=generation_job_id,
            group_id=group_id,
            url=url
        )

    @classmethod
    async def before_save(cls, instance: "GeneratedImage") -> None:
        instance.updated_at = datetime.utcnow()

