from beanie import Document, PydanticObjectId
from beanie.odm.fields import IndexModel
from datetime import datetime
from typing import Optional

class User(Document):
    workos_id: str 
    email: str
    first_name: str
    last_name: str
    email_verified: bool
    profile_picture_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_signed_in: Optional[datetime] = None

    class Settings:
        name = "users"
        use_state_management = True
        indexes = [
            IndexModel(
                "workos_id",
                unique=True
            )
        ]

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            PydanticObjectId: lambda v: str(v)  # Add this line
        }

    @classmethod
    async def before_save(cls, instance: "User") -> None:
        now = datetime.utcnow()
        if instance.created_at is None:
            instance.created_at = now
        instance.updated_at = now

    @classmethod
    def from_workos(cls, workos_user: dict):
        return cls(
            workos_id=workos_user["id"],
            email=workos_user["email"],
            first_name=workos_user["first_name"],
            last_name=workos_user["last_name"],
            email_verified=workos_user["email_verified"],
            profile_picture_url=workos_user.get("profile_picture_url"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_signed_in=datetime.utcnow()
        )

    async def update_from_workos(self, workos_user: dict):
        self.email = workos_user["email"]
        self.first_name = workos_user["first_name"]
        self.last_name = workos_user["last_name"]
        self.email_verified = workos_user["email_verified"]
        self.profile_picture_url = workos_user.get("profile_picture_url")
        self.updated_at = datetime.utcnow() 
        self.last_signed_in = datetime.utcnow()
        await self.save()

    async def update_last_signed_in(self):
        self.last_signed_in = datetime.utcnow()
        await self.save()
