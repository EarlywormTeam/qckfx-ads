from beanie import Document, PydanticObjectId
from beanie.odm.fields import IndexModel
from datetime import datetime
from typing import List, Optional, Dict
import random
import string

class Product(Document):
    name: str
    organization_id: PydanticObjectId 
    created_by_user_id: PydanticObjectId
    primary_image_url: str
    additional_image_urls: List[str] = []
    model_id: Optional[str] = None
    stage: str  # 'queued', 'in_progress', 'completed', 'error'
    log: str = ""  
    created_at: datetime
    updated_at: datetime
    background_removed_image_id: Optional[str] = None  
    background_removed_image_url: Optional[str] = None  
    description: Optional[str] = None  
    lora_weights_blob_id: Optional[str] = None
    lora_weights_blob_url: Optional[str] = None
    trigger_word: str

    @staticmethod
    def generate_trigger_word():
        length = random.randint(5, 12)
        return ''.join(random.choices(string.ascii_uppercase, k=length))

    class Settings:
        name = "products"
        use_state_management = True
        indexes = [
            IndexModel(
                ("organization_id", "name"),
                unique=True
            ),
            IndexModel(  
                ("stage", "created_at")
            )
        ]

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            PydanticObjectId: lambda v: str(v)
        }

    @classmethod
    async def before_save(cls, instance: "Product") -> None:
        now = datetime.utcnow()
        if instance.created_at is None:
            instance.created_at = now
        instance.updated_at = now

    @classmethod
    def create(cls, name: str, 
               organization_id: PydanticObjectId,
               created_by_user_id: PydanticObjectId, 
               primary_image_url: str, 
               model_id: str, 
               additional_image_urls: Optional[List[str]] = None):
        return cls(
            name=name,
            organization_id=organization_id,
            created_by_user_id=created_by_user_id,
            primary_image_url=primary_image_url,
            additional_image_urls=additional_image_urls or [],
            model_id=model_id,
            stage="queued",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            trigger_word=cls.generate_trigger_word()
        )

    async def update_stage(self, new_stage: str):
        self.stage = new_stage
        self.updated_at = datetime.utcnow()
        await self.save()

    async def add_log_entry(self, entry: str):
        self.log += f"\n{entry}" if self.log else entry
        self.updated_at = datetime.utcnow()
        await self.save()

    async def set_background_removed_image(self, blob_id: str, blob_url: str):
        self.background_removed_image_id = blob_id
        self.background_removed_image_url = blob_url
        await self.add_log_entry(f"Background removed image set with blob ID: {blob_id}")
        self.updated_at = datetime.utcnow()
        await self.save()

    async def set_description(self, description: str):
        self.description = description
        await self.add_log_entry(f"Product description set: {description}")
        self.updated_at = datetime.utcnow()
        await self.save()

    async def set_lora_weights(self, blob_id: str, blob_url: str):
        self.lora_weights_blob_id = blob_id
        self.lora_weights_blob_url = blob_url
        await self.add_log_entry(f"LoRA weights set with blob ID: {blob_id}")
        self.updated_at = datetime.utcnow()
        await self.save()
