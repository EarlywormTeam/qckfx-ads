from typing import List, Optional
from pydantic import BaseModel

class ImageSearchRequest(BaseModel):
    text: Optional[str] = None
    dominant_colors: Optional[List[str]] = None  # List of hex colors
    faces: Optional[List[str]] = None  # List of Face IDs
    products: Optional[List[str]] = None  # List of Product IDs
    page: Optional[int] = 1
    page_size: Optional[int] = 20