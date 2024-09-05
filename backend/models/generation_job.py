from beanie import Document, Indexed, PydanticObjectId
from beanie.odm.fields import IndexModel
from datetime import datetime
from typing import Optional, List
from pydantic import Field

class GenerationJob(Document):
    org_id: Indexed(PydanticObjectId)
    user_id: Indexed(PydanticObjectId)
    product_id: Indexed(PydanticObjectId)
    image_group_ids: List[PydanticObjectId]
    prompt: str
    count: int = 1
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    log: List[str] = Field(default_factory=list)

    class Settings:
        name = "generation_jobs"
        use_state_management = True
        indexes = [
            IndexModel(
                ("org_id", "user_id", "product_id"),
                unique=False
            )
        ]

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            PydanticObjectId: lambda v: str(v)
        }

    @classmethod
    async def before_save(cls, instance: "GenerationJob") -> None:
        now = datetime.utcnow()
        if instance.created_at is None:
            instance.created_at = now
        instance.updated_at = now

    @property
    def job_id(self) -> str:
        return str(self.id)

    async def update_status(self, new_status: str):
        self.status = new_status
        self.updated_at = datetime.utcnow()
        await self.save()

    async def add_log_entry(self, entry: str):
        self.log.append(entry)
        await self.save()

    @classmethod
    def create_job(cls, org_id: PydanticObjectId, user_id: PydanticObjectId, product_id: PydanticObjectId, prompt: str, count: int, image_group_ids: List[PydanticObjectId]):
        return cls(
            org_id=org_id,
            user_id=user_id,
            product_id=product_id,
            prompt=prompt,
            count=count,
            image_group_ids=image_group_ids,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )



