from typing import List, Optional
from pydantic import BaseModel

class AvatarPreviewImage(BaseModel):
    preview_image_16_9: Optional[str]
    preview_image_1_1: Optional[str]
    preview_image_9_16: Optional[str]

class AvatarResponse(BaseModel):
    id: str
    name: str
    gender: str
    preview_images: AvatarPreviewImage

class AvatarListResponse(BaseModel):
    avatars: List[AvatarResponse]
