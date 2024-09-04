from beanie import Document, PydanticObjectId
from beanie.odm.fields import IndexModel
from datetime import datetime
from typing import Dict, List

from models.user import User

class Organization(Document):
    workos_id: str
    name: str
    created_at: datetime
    updated_at: datetime
    allow_profiles_outside_organization: bool
    domains: List[Dict[str, str]]

    class Settings:
        name = "organizations"
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
            PydanticObjectId: lambda v: str(v)
        }

    @classmethod
    async def before_save(cls, instance: "Organization") -> None:
        now = datetime.utcnow()
        if instance.created_at is None:
            instance.created_at = now
        instance.updated_at = now

    @classmethod
    def from_workos(cls, workos_org: dict):
        return cls(
            workos_id=workos_org["id"],
            name=workos_org["name"],
            created_at=datetime.fromisoformat(workos_org["created_at"].rstrip('Z')),
            updated_at=datetime.fromisoformat(workos_org["updated_at"].rstrip('Z')),
            allow_profiles_outside_organization=workos_org["allow_profiles_outside_organization"],
            domains=[{
                "id": domain["id"],
                "domain": domain["domain"],
                "organization_id": domain["organization_id"]
            } for domain in workos_org.get("domains", [])]
        )

    async def update_from_workos(self, workos_org: dict):
        self.name = workos_org["name"]
        self.updated_at = datetime.fromisoformat(workos_org["updated_at"].rstrip('Z'))
        self.allow_profiles_outside_organization = workos_org["allow_profiles_outside_organization"]
        self.domains = [{
            "id": domain["id"],
            "domain": domain["domain"],
            "organization_id": domain["organization_id"]
        } for domain in workos_org.get("domains", [])]
        await self.save()


class OrganizationMembership(Document):
    user_id: PydanticObjectId
    organization_id: PydanticObjectId 
    role: Dict[str, str]
    status: str
    created_at: datetime
    updated_at: datetime
    workos_id: str 

    class Settings:
        name = "organization_memberships"
        use_state_management = True
        indexes = [
            IndexModel(
                ("user_id", "organization_id"),
                unique=True
            )
        ]

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            PydanticObjectId: lambda v: str(v)
        }

    @classmethod
    async def before_save(cls, instance: "OrganizationMembership") -> None:
        now = datetime.utcnow()
        if instance.created_at is None:
            instance.created_at = now
        instance.updated_at = now

    @classmethod
    def from_workos(cls, workos_org_membership: dict, user: User, organization: Organization):
        return cls(
            workos_id=workos_org_membership["id"],
            user_id=user.id,
            organization_id=organization.id,
            role=workos_org_membership["role"],
            status=workos_org_membership["status"],
            created_at=datetime.fromisoformat(workos_org_membership["created_at"].rstrip('Z')),
            updated_at=datetime.fromisoformat(workos_org_membership["updated_at"].rstrip('Z'))
        )

    async def update_from_workos(self, workos_org_membership: dict, organization: Organization, user: User):
        self.workos_id = workos_org_membership["id"]
        self.organization_id = organization.id
        self.user_id = user.id
        self.role = workos_org_membership["role"]
        self.status = workos_org_membership["status"]
        self.updated_at = datetime.utcnow()
        await self.save()

