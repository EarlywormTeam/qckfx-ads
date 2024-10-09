import uuid
from io import BytesIO
import base64

from beanie import PydanticObjectId

from toolbox import Toolbox
from toolbox.services.blob_storage import BlobStorageService
from toolbox.services.image.process_image_for_search import ImageSearchMetadata
from models.image import Image, Dimensions
from models.face import Face
from toolbox.services.image.process_image_for_search import ImageAlreadyExistsError
from models.tag import Tag

# Extracts: 
# - dominant colors
# - aspect ratio
# - dimensions
# - file size
# - file type
# - file resolution
# - facial detection
# - product detection
# - outfit detection
# - caption (including people, places, objects, etc.)
# - tags: 
#   - people (couple, group, single, age (baby, youth, teen, adult, senior), gender (male, female, non-binary), ethnicity (white, black, asian, latino, native american, etc.), clothing (casual, formal, swimwear, etc.), accessories (jewelry, glasses, hat, etc.), pose (action, dance, etc.))
#   - lighting (ambient, daylight, night, studio, strobe, lifestyle, portrait, etc.)
#   - emotions (happy, sad, angry, gloomy, casual, formal, etc.)
#   - event (wedding, birthday, graduation, fundraiser, conference, anniversary, etc.)
#   - objects (furniture, plants, food, drinks, etc.)
#   - regions (forest, mountains, desert, ocean, building, etc.)
#   - orientation (portrait, landscape, square)
#   - focus (macro, close-up, wide, etc.)
#   - time (morning, afternoon, evening, night)
#   - weather (sunny, rainy, snowy, windy, cloudy, etc.)

async def background_process_uploaded_image(toolbox: Toolbox, creation_method: str, user_id: PydanticObjectId, organization_id: PydanticObjectId, blob_path: str):
    print("Indexing image", blob_path)
    blob_storage = toolbox.services.blob_storage
    image_data = await blob_storage.download_blob(blob_path, BlobStorageService.ContainerName.UPLOADS)

    image_service = toolbox.services.image_service
    
    try:
        image_info: ImageSearchMetadata = await image_service.process_image_for_search(image_data, organization_id)
        print("Image info gathering complete")
        
        # Re-upload the image to the PROCESSED container
        processed_blob_path = f"{organization_id}/{uuid.uuid4()}.{image_info.basic_details.file_type.lower()}"
        await blob_storage.upload_blob(
            processed_blob_path,
            image_data,
            BlobStorageService.ContainerName.PROCESSED
        )

        print("Image re-uploaded to processed container")

        # Create an embedding for the image caption
        llm_service = toolbox.services.llm
        caption_embedding = await llm_service.create_embedding(image_info.image_caption)

        print("Caption embedding created")

        # Create or get existing tags
        tags = []
        tag_categories = [
            ("people", image_info.image_tags.people),
            ("lighting", image_info.image_tags.lighting),
            ("emotions", image_info.image_tags.emotions),
            ("event", image_info.image_tags.event),
            ("objects", image_info.image_tags.objects),
            ("regions", image_info.image_tags.regions),
            ("orientation", image_info.image_tags.orientation),
            ("focus", image_info.image_tags.focus),
            ("time", image_info.image_tags.time),
            ("weather", image_info.image_tags.weather)
        ]

        for category, tag_names in tag_categories:
            for tag_name in tag_names:
                full_tag_name = f"{category}-{tag_name}"
                existing_tag = await Tag.find_one({"name": full_tag_name, "category": category, "organization": organization_id})
                if existing_tag:
                    tags.append(existing_tag)
                else:
                    new_tag = Tag(name=full_tag_name, category=category, organization=organization_id)
                    await new_tag.save()
                    tags.append(new_tag)

        print("Tags created or retrieved")

        # Create and save Image document
        image = Image(
            organization=organization_id,
            created_by_user=user_id,
            creation_method=creation_method,
            file_path=processed_blob_path,
            phash=image_info.basic_details.phash,
            dimensions=Dimensions(
                width=image_info.basic_details.width,
                height=image_info.basic_details.height,
                aspect_ratio=image_info.basic_details.aspect_ratio
            ),
            resolution=image_info.basic_details.resolution,
            format=image_info.basic_details.file_type,
            dominant_colors=image_info.dominant_colors,
            detected_products=image_info.product_details.detections,
            caption=image_info.image_caption,
            caption_embedding=caption_embedding,
            tags=tags
        )
        await image.save()

        print("Image document created")

        # Upload face images to the faces container
        face_file_paths = []
        for i, aligned_face_base64 in enumerate(image_info.facial_details.aligned_faces):
            
            # Decode the base64 string to bytes
            face_image_bytes = base64.b64decode(aligned_face_base64)

            # Generate a unique filename for the face image
            file_ext = image_info.basic_details.file_type.lower()
            face_filename = f"{uuid.uuid4()}.{file_ext}"
            # Use only the organization ID in the path
            face_blob_path = f"{organization_id}/{face_filename}"

            # Upload the face image to the faces container
            await blob_storage.upload_blob(
                face_blob_path,
                face_image_bytes,
                BlobStorageService.ContainerName.FACES
            )
            face_file_paths.append(face_blob_path)

        print("Face images uploaded")

        # Create and save Face documents
        for i, _ in enumerate(image_info.facial_details.aligned_faces):
            # Check if a face with the same phash already exists in the organization
            face_phash = image_info.facial_details.phashes[i]
            existing_face = await Face.find_one({
                "organization": organization_id,
                "phash": face_phash,
                "image.phash": image_info.basic_details.phash
            })

            if existing_face:
                print(f"Face with phash {face_phash} already exists in the organization. Skipping.")
                # Delete the existing face image from blob storage
                try:
                    await blob_storage.delete_blob(existing_face.file_path, BlobStorageService.ContainerName.FACES)
                    print(f"Deleted existing face image: {existing_face.file_path}")
                except Exception as e:
                    print(f"Error deleting existing face image: {str(e)}")
                continue
            
            face = Face(
                image=image,
                file_path=face_file_paths[i],
                organization=organization_id,
                face_embedding=image_info.facial_details.face_embeddings[i],
                bounding_box=image_info.facial_details.bounding_boxes[i],
                detection_confidence=image_info.facial_details.confidence_levels[i],
                phash=image_info.facial_details.phashes[i]
            )
            await face.save()
            image.faces.append(face)

        print("Face documents created")

        # Update Image document with face references
        await image.save()

        print("Image document updated")

    except ImageAlreadyExistsError as e:
        print(f"Duplicate image detected: {str(e)}")
        # Remove the image from the uploads container
        try:
            await blob_storage.delete_blob(blob_path, BlobStorageService.ContainerName.UPLOADS)
            print(f"Duplicate image removed from uploads container: {blob_path}")
        except Exception as delete_error:
            print(f"Error removing duplicate image from uploads container: {str(delete_error)}")
        return

    await blob_storage.delete_blob(blob_path, BlobStorageService.ContainerName.UPLOADS)

    print("Image deleted from uploads container")