from typing import Tuple
from io import BytesIO
from PIL import Image
from pydantic import BaseModel, Field
import imagehash

class ImageDetails(BaseModel):
    aspect_ratio: float = Field(..., description="The aspect ratio of the image")
    width: int = Field(..., description="The width of the image in pixels")
    height: int = Field(..., description="The height of the image in pixels")
    file_size: int = Field(..., description="The size of the image file in bytes")
    file_type: str = Field(..., description="The file type/format of the image")
    resolution: int = Field(..., description="The resolution of the image in DPI (average of width and height)")
    phash: str = Field(..., description="The perceptual hash of the image")

def extract_basic_details(image_data: bytes) -> ImageDetails:
    """
    Extract basic details from image data.
    
    Args:
    image_data (bytes): Image data in bytes.
    
    Returns:
    ImageDetails: Object containing basic image details.
    """
    # Read the image from bytes
    image = Image.open(BytesIO(image_data))
    
    # Get image dimensions
    width, height = image.size
    
    # Calculate aspect ratio
    aspect_ratio = width / height
    
    # Get file size
    file_size = len(image_data)
    
    # Get file type
    file_type = image.format
    
    # Get file resolution (DPI)
    resolution = image.info.get('dpi', (72, 72))  # Default to 72 DPI if not available
    avg_resolution = int(sum(resolution) / len(resolution))
    
    # Calculate perceptual hash
    phash = str(imagehash.phash(image))
    
    return ImageDetails(
        aspect_ratio=round(aspect_ratio, 2),
        width=width,
        height=height,
        file_size=file_size,
        file_type=file_type,
        resolution=avg_resolution,
        phash=phash
    )

# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Please provide an image path as an argument.")
        sys.exit(1)

    image_path = sys.argv[1]

    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{image_path}' was not found.")
        sys.exit(1)
    except IOError:
        print(f"Error: Unable to read the file '{image_path}'.")
        sys.exit(1)

    details = extract_basic_details(image_data)

    for field in details.__dataclass_fields__:
        value = getattr(details, field)
        print(f"{field.replace('_', ' ').title()}: {value}")
