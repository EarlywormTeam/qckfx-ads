from skimage import color
import numpy as np
from sklearn.cluster import KMeans
from typing import List, Dict
from io import BytesIO
from PIL import Image
from pydantic import BaseModel, Field

class LABColor(BaseModel):
    l: float = Field(..., ge=0, le=100)
    a: float = Field(..., ge=-128, le=127)
    b: float = Field(..., ge=-128, le=127)

def extract_dominant_colors(image_data: bytes, num_colors: int = 10) -> List[Dict[str, float]]:
    """
    Extract the dominant colors from image data and convert them to LAB color space.
    
    Args:
    image_data (bytes): Image data in bytes.
    num_colors (int): Number of dominant colors to extract (default is 10).
    
    Returns:
    List[Dict[str, float]]: List of dominant colors as dictionaries with 'vector' and 'percentage' keys.
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
    lab_colors = color.rgb2lab(sorted_colors.reshape(1, -1, 3)).reshape(-1, 3)
    
    # Calculate the percentage of each color
    percentages = counts[sorted_indices] / len(labels)

    # Create the list of dominant colors in the required format
    dominant_colors = [
        {
            "vector": [float(l), float(a), float(b)],
            "percentage": float(percentage)
        }
        for (l, a, b), percentage in zip(lab_colors, percentages)
    ]

    return dominant_colors

# Example usage
if __name__ == "__main__":
    import sys
    import matplotlib.pyplot as plt

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

    dominant_colors = extract_dominant_colors(image_data)

    # Display the dominant colors
    plt.imshow([dominant_colors])
    plt.title("Top 10 Dominant Colors")
    plt.axis('off')
    plt.show()

    # Print the RGB values
    for i, color in enumerate(dominant_colors, 1):
        print(f"Color {i}: RGB{tuple(round(c * 255) for c in color)}")
