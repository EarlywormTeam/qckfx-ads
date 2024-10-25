from typing import List, Optional
from beanie import PydanticObjectId 
from pydantic import BaseModel, Field
from models.image import Dimensions

class ImageResponseModel(BaseModel):
    id: PydanticObjectId = Field(..., alias="_id", description="Id of the image")
    creation_method: str = Field(..., description="Method used to create the image (generated or uploaded)")
    url: str = Field(..., description="Url to the image file")
    dimensions: Dimensions = Field(..., description="Dimensions of the image")
    resolution: int = Field(..., description="Resolution of the image in DPI")
    format: str = Field(..., description="File format of the image")
    caption: Optional[str] = Field(None, description="Caption describing the image")

class ImageSearchResponse(BaseModel):
    images: List[ImageResponseModel]
    total: int
    page: int
    page_size: int
    total_pages: int