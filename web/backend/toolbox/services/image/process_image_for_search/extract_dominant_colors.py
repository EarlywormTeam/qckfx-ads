import skimage
import numpy as np
from sklearn.cluster import KMeans
from typing import List, Dict
from io import BytesIO
from PIL import Image
from pydantic import BaseModel, Field
from models.color import Color
from beanie import PydanticObjectId
from models.image import DominantColor
import asyncio

class LABColor(BaseModel):
    l: float = Field(..., ge=0, le=100)
    a: float = Field(..., ge=-128, le=127)
    b: float = Field(..., ge=-128, le=127)

async def extract_dominant_colors(image_data: bytes, organization_id: PydanticObjectId, num_colors: int = 10) -> List[DominantColor]:
    """
    Extract the dominant colors from image data, convert them to LAB color space,
    and store them in the database if they don't exist.
    
    Args:
    image_data (bytes): Image data in bytes.
    organization_id (PydanticObjectId): ID of the organization.
    num_colors (int): Number of dominant colors to extract (default is 10).
    
    Returns:
    List[DominantColor]: List of dominant colors with their percentages.
    """
    # Read the image from bytes
    image = Image.open(BytesIO(image_data))
    
    # Convert image to RGB mode if it's not already
    image = image.convert('RGB')
    
    # Convert image to numpy array
    image_array = np.array(image)
    
    # Reshape the image to be a list of pixels
    pixels = image_array.reshape((-1, 3))
    
    # Convert to float type
    pixels = np.float32(pixels)
    
    # Perform k-means clustering
    kmeans = KMeans(n_clusters=num_colors, random_state=42)
    kmeans.fit(pixels)
    
    # Get the colors
    colors = kmeans.cluster_centers_
    
    # Convert colors to 0-1 range
    colors = colors / 255.0
    
    # Sort colors by cluster size
    labels = kmeans.labels_
    counts = np.bincount(labels)
    sorted_indices = np.argsort(counts)[::-1]
    
    sorted_colors = colors[sorted_indices]
    
    # Convert RGB colors to LAB
    lab_colors = skimage.color.rgb2lab(sorted_colors.reshape(1, -1, 3)).reshape(-1, 3)
    
    # Calculate the percentage of each color
    percentages = counts[sorted_indices] / len(labels)

    dominant_colors = []

    for lab_vector, percentage in zip(lab_colors, percentages):
        # Check if the color already exists in the database
        existing_color = await Color.find_one({"lab_vector": lab_vector.tolist(), "organization": organization_id})
        
        if existing_color:
            color = existing_color
        else:
            # Create a new Color document
            color = Color(lab_vector=lab_vector.tolist(), organization=organization_id)
            await color.insert()

        dominant_colors.append(DominantColor(color=color, percentage=float(percentage)))

    return dominant_colors

# Example usage
if __name__ == "__main__":
    import sys
    import matplotlib.pyplot as plt
    from beanie import init_beanie
    from motor.motor_asyncio import AsyncIOMotorClient

    async def main():
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

        # Initialize database connection (replace with your actual database URL)
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        await init_beanie(database=client.db_name, document_models=[Color])

        # Use a dummy organization ID for this example
        organization_id = PydanticObjectId("5f7b5e7a1c9d440000d5a3b1")

        dominant_colors = await extract_dominant_colors(image_data, organization_id)

        # Display the dominant colors
        plt.imshow([[color.color.lab_vector for color in dominant_colors]])
        plt.title("Top 10 Dominant Colors")
        plt.axis('off')
        plt.show()

        # Print the LAB values and percentages
        for i, color in enumerate(dominant_colors, 1):
            print(f"Color {i}: LAB{color.color.lab_vector}, Percentage: {color.percentage:.2f}")

    asyncio.run(main())
