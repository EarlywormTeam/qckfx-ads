from pydantic import BaseModel
from typing import List, Optional, Dict

class ProductResponse(BaseModel):
    id: str
    name: str
    organization_id: str
    created_by: Dict[str, str] = {
        "id": str,
        "name": str
    }
    primary_image_url: str
    additional_image_urls: List[str]
    stage: str
    log: str
    created_at: str
    updated_at: str
    background_removed_image_url: Optional[str] = None
    description: Optional[str] = None

class ProductsListResponse(BaseModel):
    products: List[ProductResponse]