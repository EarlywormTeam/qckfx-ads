import numpy as np
from typing import List, Any
from io import BytesIO
from PIL import Image
from deepface import DeepFace
import matplotlib.pyplot as plt
import base64
from pydantic import BaseModel, Field
from models.face import BoundingBox
import imagehash  

class FacialDetails(BaseModel):
    face_embeddings: List[List[float]] = Field(default_factory=list)
    aligned_faces: List[str] = Field(default_factory=list)
    confidence_levels: List[float] = Field(default_factory=list)
    bounding_boxes: List[BoundingBox] = Field(default_factory=list)
    phashes: List[str] = Field(default_factory=list)  

def extract_facial_details(image_data: bytes) -> FacialDetails:
    """
    Extract facial details from image data using DeepFace and FaceNet.

    Args:
        image_data (bytes): Image data in bytes.

    Returns:
        FacialDetails: Object containing face embeddings, aligned facial images, and confidence levels.
    """
    # Convert image bytes to PIL Image
    image = Image.open(BytesIO(image_data)).convert('RGB')

    # Convert PIL Image to numpy array
    img_array = np.array(image)

    # Get face embeddings using FaceNet
    try:
        represent = DeepFace.represent(
            img_path=img_array,
            model_name='Facenet',
            enforce_detection=False,
            detector_backend='retinaface'
        )
        # Extract only the embedding vectors
        embeddings = [item['embedding'] for item in represent] if isinstance(represent, list) else [represent['embedding']]
    except Exception as e:
        print(f"Error in DeepFace.represent: {e}")
        embeddings = []

    # Extract aligned facial images and confidence levels
    try:
        faces = DeepFace.extract_faces(
            img_path=img_array,
            align=True,
            enforce_detection=False,
            detector_backend='retinaface'
        )
    except Exception as e:
        print(f"Error in DeepFace.extract_faces: {e}")
        faces = []

    aligned_faces = []
    confidence_levels = []
    bounding_boxes = []
    phashes = []  # Add this list
    for face in faces:
        face_array = face['face'][:, :, ::-1]  # Convert BGR to RGB
        # Check the data type and scale if necessary
        if face_array.dtype != np.uint8:
            # If the pixel values are in [0, 1], scale to [0, 255]
            if face_array.max() <= 1.0:
                face_array = (face_array * 255).astype(np.uint8)
            else:
                face_array = face_array.astype(np.uint8)
        aligned_face = Image.fromarray(face_array)
        
        # Convert PIL Image to base64 encoded string
        buffered = BytesIO()
        aligned_face.save(buffered, format="PNG")
        aligned_face_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        aligned_faces.append(aligned_face_base64)
        confidence_levels.append(face['confidence'])  # Add this line
        bounding_boxes.append(BoundingBox(  # Updated to use the BoundingBox class
            x=face['facial_area']['x'],
            y=face['facial_area']['y'],
            width=face['facial_area']['w'],
            height=face['facial_area']['h']
        ))
        
        # Calculate and store the pHash
        phash = str(imagehash.phash(aligned_face))
        phashes.append(phash)

    return FacialDetails(
        face_embeddings=embeddings,
        aligned_faces=aligned_faces,
        confidence_levels=confidence_levels,
        bounding_boxes=bounding_boxes,
        phashes=phashes  # Add this field
    )

def display_facial_details(face_embeddings: List[List[float]],
                           aligned_faces: List[str],  # Changed to List[str]
                           confidence_levels: List[float],
                           bounding_boxes: List[BoundingBox],  # Updated type hint
                           original_image: Image.Image):
    """
    Display the extracted facial details using matplotlib.

    Args:
        face_embeddings (List[List[float]]): List of face embeddings.
        aligned_faces (List[Image.Image]): List of aligned face images.
        confidence_levels (List[float]): List of confidence levels for each face.
        bounding_boxes (List[BoundingBox]): List of bounding boxes for each face.
        original_image (Image.Image): The original image.
    """
    num_faces = len(aligned_faces)
    if num_faces == 0:
        print("No faces detected to display.")
        return

    # Adjust subplot dimensions based on number of faces
    fig, axs = plt.subplots(num_faces, 2, figsize=(10, 5 * num_faces))

    # If only one face is detected, axs is not a list of lists
    if num_faces == 1:
        axs = [axs]

    for idx in range(num_faces):
        ax_face, ax_embedding = axs[idx] if num_faces > 1 else axs

        # Display Aligned Face
        aligned_face = Image.open(BytesIO(base64.b64decode(aligned_faces[idx])))
        ax_face.imshow(aligned_face)
        ax_face.set_title(f"Aligned Face {idx + 1}\nConfidence: {confidence_levels[idx]:.2f}")  # Update this line
        ax_face.axis('off')

        # Display Face Embedding as a heatmap
        embedding = face_embeddings[idx] if idx < len(face_embeddings) else []
        if isinstance(embedding, list) and all(isinstance(x, (float, int)) for x in embedding):
            embedding_array = np.array(embedding).reshape(1, -1)
            ax_embedding.imshow(embedding_array, aspect='auto', cmap='viridis')
            ax_embedding.set_title(f"Face Embedding {idx + 1}")
            ax_embedding.axis('off')
        else:
            ax_embedding.text(0.5, 0.5, "No Embedding Available", fontsize=12, ha='center', va='center')
            ax_embedding.set_title(f"Face Embedding {idx + 1}")
            ax_embedding.axis('off')

    # Display original image with bounding boxes
    axs[0, 0].imshow(original_image)
    axs[0, 0].set_title("Original Image with Bounding Boxes")
    for bbox in bounding_boxes:
        rect = plt.Rectangle((bbox.x, bbox.y), bbox.width, bbox.height,
                             fill=False, edgecolor='red', linewidth=2)
        axs[0, 0].add_patch(rect)
    axs[0, 0].axis('off')

    plt.tight_layout()
    plt.show()

def main():
    """
    Sample main function to test the facial details extraction script.
    """
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

    results = extract_facial_details(image_data)

    # Display the results
    display_facial_details(results.face_embeddings, results.aligned_faces, results.confidence_levels, results.bounding_boxes, Image.open(image_path))  # Update this line

    # Print Face Embeddings, Confidence Levels, and pHashes
    if results.face_embeddings:
        for idx, (embedding, confidence, phash) in enumerate(zip(results.face_embeddings, results.confidence_levels, results.phashes), 1):
            print(f"\nFace {idx}:")
            print(f"Confidence: {confidence:.2f}")
            print(f"pHash: {phash}")
            print("Embedding:")
            print(embedding)
    else:
        print("No face embeddings available.")

if __name__ == "__main__":
    main()