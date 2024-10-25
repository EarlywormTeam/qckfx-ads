from fastapi import Request
from beanie import PydanticObjectId
import numpy as np
import skimage.color
from models import Image, Color
from toolbox import Toolbox
from api.request_types.search import ImageSearchRequest 
from api.response_types.search import ImageSearchResponse
from toolbox.services.blob_storage import BlobStorageService, BlobSasPermissions

async def perform_image_search(
    organization_id: str,
    request: Request,
    image_search_request: ImageSearchRequest,
    toolbox
) -> ImageSearchResponse:
    toolbox: Toolbox = request.state.toolbox 
    
    query = [{"$match": {"organization.$id": PydanticObjectId(organization_id)}}]

    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return np.array([int(hex_color[i:i+2], 16) for i in (0, 2, 4)]) / 255.0

    rgb_colors = np.array([hex_to_rgb(color) for color in image_search_request.dominant_colors])
    lab_colors = skimage.color.rgb2lab(rgb_colors.reshape(1, -1, 3)).reshape(-1, 3)

    if image_search_request.text:

        # Vectorize the search query using LLMService
        llm_service = toolbox.services.llm
        query_embedding = await llm_service.create_embedding(image_search_request.text)

        # Search in caption or tags
        query = [{
            "$vectorSearch": {
                "exact": True,
                "filter": {
                    "organization.$id": PydanticObjectId(organization_id)
                },
                "index": "qckfx_image_vector_index",
                "limit": image_search_request.page_size,
                # "numCandidates": image_search_request.page_size * 20,
                "path": "caption_embedding",
                "queryVector": query_embedding,
            }
        }]

        if image_search_request.products:
            query[0]["$vectorSearch"]["filter"]["detected_products.$id"] = {"$in": [PydanticObjectId(product_id) for product_id in image_search_request.products]}

    elif image_search_request.products:
        print("Product Search")
        query = [
            {
                "$match": {
                    "detected_products.$id": {"$in": [PydanticObjectId(product_id) for product_id in image_search_request.products]}
                }
            },
            {
                "$match": {
                    "organization.$id": PydanticObjectId(organization_id)
                }
            },
            {
                "$skip": (image_search_request.page - 1) * image_search_request.page_size
            },
            {
                "$limit": image_search_request.page_size
            }
        ]

    elif image_search_request.dominant_colors:
        print("Color Search")
        cutoff_distance = 25.0  # Define a cutoff distance in Lab space
        query = [{
            "$vectorSearch": {
                "exact": True,
                "filter": {
                    "organization.$id": PydanticObjectId(organization_id)
                },
                "index": "qckfx_color_vector_index",
                "limit": image_search_request.page_size,
                # "numCandidates": image_search_request.page_size * 20,
                "path": "lab_vector",
                "queryVector": lab_colors[0].tolist(),
            }
        }]
        
        # Aggregate to find colors within the cutoff distance
        colors = await Color.aggregate([
            {
                "$vectorSearch": {
                    "exact": True,
                    "filter": {
                        "organization.$id": PydanticObjectId(organization_id)
                    },
                    "index": "qckfx_color_vector_index",
                    "limit": 100,  # Increase limit to fetch more candidates
                    "path": "lab_vector",
                    "queryVector": lab_colors[0].tolist(),
                }
            },
            {
                "$addFields": {
                    "distance": {
                        "$sqrt": {
                            "$add": [  # Use $add instead of $sum for proper aggregation
                                {"$pow": [
                                    {"$subtract": [
                                        {"$arrayElemAt": ["$lab_vector", 0]}, 
                                        lab_colors[0][0]
                                    ]}, 
                                    2
                                ]},
                                {"$pow": [
                                    {"$subtract": [
                                        {"$arrayElemAt": ["$lab_vector", 1]}, 
                                        lab_colors[0][1]
                                    ]}, 
                                    2
                                ]},
                                {"$pow": [
                                    {"$subtract": [
                                        {"$arrayElemAt": ["$lab_vector", 2]}, 
                                        lab_colors[0][2]
                                    ]}, 
                                    2
                                ]}
                            ]
                        }
                    }
                }
            },
            {
                "$match": {
                    "distance": {"$lte": cutoff_distance}
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "distance": 1
                }
            }
        ]).to_list()

        print(colors)

        if not colors:
            # If no colors are within the cutoff distance, return empty response early
            return ImageSearchResponse(
                images=[],
                total=0,
                page=image_search_request.page,
                page_size=image_search_request.page_size,
                total_pages=0
            )

        # Assign weights based on distance and percentage
        query = [
            {
                "$match": {
                    "organization.$id": PydanticObjectId(organization_id),
                    "dominant_colors.color._id": {"$in": [color["_id"] for color in colors]}
                }
            },
            {
                "$addFields": {
                    "weightedColorMatches": {
                        "$map": {
                            "input": colors,
                            "as": "color",
                            "in": {
                                "colorId": "$$color._id",
                                "distance": "$$color.distance",
                                "weight": {
                                    "$cond": [
                                        {"$gt": ["$$color.distance", 0]},
                                        {"$divide": [cutoff_distance, "$$color.distance"]},
                                        1
                                    ]
                                }
                            }
                        }
                    },
                    "maxWeightedColorPercentage": {
                        "$reduce": {
                            "input": "$dominant_colors",
                            "initialValue": 0,
                            "in": {
                                "$max": [
                                    "$$value",
                                    {
                                        "$let": {
                                            "vars": {
                                                "matchingColor": {
                                                    "$arrayElemAt": [
                                                        {
                                                            "$filter": {
                                                                "input": "$weightedColorMatches",
                                                                "as": "match",
                                                                "cond": {"$eq": ["$$match.colorId", "$$this.color._id"]}
                                                            }
                                                        }, 
                                                        0
                                                    ]
                                                }
                                            },
                                            "in": {
                                                "$multiply": [
                                                    "$$matchingColor.weight",
                                                    "$$this.percentage"
                                                ]
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            },
            {
                "$sort": {"maxWeightedColorPercentage": -1}
            },
            {
                "$skip": (image_search_request.page - 1) * image_search_request.page_size
            },
            {
                "$limit": image_search_request.page_size
            }
        ]

    # if search.dominant_colors:
    #     # Example: Match any dominant color vectors (simplistic approach)
    #     color_queries = [{"dominant_colors.vector": {"$all": color}} for color in search.dominant_colors]
    #     query["$and"] = color_queries

    # if search.faces:
    #     query["faces"] = {"$in": search.faces}

    # page = search.page if search.page and search.page > 0 else 1
    # page_size = search.page_size if search.page_size and search.page_size > 0 else 20
    # skip = (page - 1) * page_size

    images = await Image.aggregate(query).to_list()

    # Generate SAS tokens for each image
    blob_service = toolbox.services.blob_storage
    for image in images:
        sas_url = await blob_service.generate_blob_sas(
            blob_name=image["file_path"],
            container_name=BlobStorageService.ContainerName.PROCESSED,
            expiry_mins=15,  # Token expires in 15 minutes
            permission=BlobSasPermissions(read=True)
        )
        image["url"] = sas_url
    
    # total_pages = (total + image_search_request.page_size - 1) // image_search_request.page_size

    return ImageSearchResponse(
        images=images,
        total=1000,
        page=image_search_request.page,
        page_size=image_search_request.page_size,
        total_pages=100
    )

# Helper functions
def hex_to_rgb(hex_color: str) -> np.ndarray:
    hex_color = hex_color.lstrip('#')
    return np.array([int(hex_color[i:i+2], 16) for i in (0, 2, 4)]) / 255.0