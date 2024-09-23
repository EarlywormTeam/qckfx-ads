# Run with: uvicorn main:app --reload
import asyncio
import os
import json 
from typing import List
import time

from beanie import PydanticObjectId
from beanie.operators import In
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from workos import AsyncWorkOSClient
import io
from starlette.middleware.base import BaseHTTPMiddleware
from urllib.parse import urlparse

from api.response_types.product import ProductResponse, ProductsListResponse
from models import GenerationJob, GeneratedImage, GeneratedImageGroup, Organization, OrganizationMembership, Product, User, init_beanie_models, WaitlistEntry
from middleware.session import SessionMiddleware
from background_jobs.generate_product_image.background_generate_product_image import background_generate_product_image
from background_jobs.refine_product_image.background_refine_product_image import background_refine_product_image
from background_jobs.train_product_lora import train_product_lora
import background_jobs.background_io_thread as background_io_thread
from toolbox import Toolbox

load_dotenv()

REDIRECT_URI = os.getenv("WORKOS_REDIRECT_URI", "http://qckfx.com/api/hooks/workos")
workos_client = AsyncWorkOSClient(api_key=os.getenv("WORKOS_API_KEY"), client_id=os.getenv("WORKOS_CLIENT_ID"))

cookie_password = os.getenv("COOKIE_PASSWORD")
if not cookie_password:
    raise ValueError("COOKIE_PASSWORD environment variable is not set")

session_middleware = SessionMiddleware(workos=workos_client, cookie_password=cookie_password)
async def verify_session(request: Request):
    await session_middleware.dispatch(request, lambda r: r)
    if not request.state.session or not request.state.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return request.state.session

class ToolboxMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.toolbox = Toolbox()
        response = await call_next(request)
        return response

app = FastAPI()
app.add_middleware(ToolboxMiddleware)

# Modify the startup event to initialize the database
@app.on_event("startup")
async def startup_event():
    await init_beanie_models()

@app.get("/api/user/organization")
async def get_user_organizations(request: Request, session: dict = Depends(verify_session)):
    user_id = session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Fetch organization memberships for the user
    memberships = await OrganizationMembership.find(OrganizationMembership.user_id == str(user.id)).to_list()
    
    # Fetch organizations based on the memberships
    organization_ids = [membership.organization_id for membership in memberships]
    organizations = await Organization.find({"_id": {"$in": organization_ids}}).to_list()
    
    # Format the response
    org_data = [
        {
            "id": str(org.id),
            "name": org.name,
            "role": next((m.role for m in memberships if m.organization_id == str(org.id)), None)
        }
        for org in organizations
    ]
    
    return {"organizations": org_data}

@app.get("/api/product", response_model=ProductsListResponse)
async def get_products(organization_id: str = None, session: dict = Depends(verify_session)):
    if not organization_id:
        raise HTTPException(400, "Missing organization_id")
    
    # Fetch products for the specified organization
    products = await Product.find(Product.organization_id == PydanticObjectId(organization_id)).to_list()

    # Convert products to the expected format
    formatted_products = []
    for product in products:
        user = await User.get(product.created_by_user_id)
        user_name = user.first_name + " " + user.last_name if user else None
        
        formatted_products.append(
            ProductResponse(
                id=str(product.id),
                name=product.name,
                organization_id=str(product.organization_id),
                created_by={
                    "id": str(product.created_by_user_id),
                    "name": user_name
                },
                primary_image_url=product.primary_image_url,
                additional_image_urls=product.additional_image_urls,
                stage=product.stage,
                log=product.log,
                created_at=product.created_at.isoformat(),
                updated_at=product.updated_at.isoformat(),
                background_removed_image_url=product.background_removed_image_url,
                description=product.description
            )
        )
    
    return ProductsListResponse(products=formatted_products)

class CreateProductRequest(BaseModel):
    name: str
    primary_image_url: str
    organization_id: str
    additional_image_urls: List[str] = Field(default_factory=list)

@app.post("/api/product")
async def create_product(request: CreateProductRequest, session: dict = Depends(verify_session)):
    user_id = session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # Get the user's organization_id
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create the product
    product = await Product.create(
        name=request.name,
        organization_id=PydanticObjectId(request.organization_id),
        created_by_user_id=user.id,
        primary_image_url=request.primary_image_url,
        additional_image_urls=request.additional_image_urls,
        model_id=None  # This will be set during the training process
    )
    
    # Kick off the training process in the background
    background_io_thread.run_async_task(train_product_lora, product)
    
    return {"product": product}

class GenerateProductImageRequest(BaseModel):
    prompt: str
    count: int

@app.post("/api/product/{product_id}/generate")
async def generate_product_image(product_id: str, body: GenerateProductImageRequest, session: dict = Depends(verify_session)):
    product = await Product.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Create new image groups, one for each count
    image_groups = []
    for _ in range(body.count):
        image_group = await GeneratedImageGroup.create(
            organization_id=product.organization_id,
            product_id=product.id,
        )
        image_group = await image_group.insert()
        image_groups.append(image_group)
    
    # Create a new generation job
    generation_job = GenerationJob.create_job(
        org_id=product.organization_id,
        user_id=PydanticObjectId(session.get("user_id")),
        product_id=PydanticObjectId(product_id),
        prompt=body.prompt,
        count=body.count,
        image_group_ids=[group.id for group in image_groups]
    )
    generation_job = await generation_job.insert()

    # Kick off the generation process in the background
    asyncio.create_task(background_io_thread.run_async_task(
        background_generate_product_image,
        body.prompt,
        body.count,
        product.id,
        generation_job.id,
        [group.id for group in image_groups]
    ))
    
    return {
        "generation_job_id": str(generation_job.id),
        "image_group_ids": [str(group.id) for group in image_groups]
    }

class RefineImageRequestBody(BaseModel):
    prompt: str

@app.post("/api/image_group/{image_group_id}/image/{image_id}/refine")
async def refine_image(image_group_id: str, image_id: str, body: RefineImageRequestBody, session: dict = Depends(verify_session)):
    image_group = await GeneratedImageGroup.get(image_group_id)
    if not image_group:
        raise HTTPException(status_code=404, detail="Image group not found")

    image = await GeneratedImage.get(image_id)
    if not image or image.group_id != image_group.id:
        raise HTTPException(status_code=404, detail="Image not found")

    # Create a new generation job for refinement
    generation_job = GenerationJob.create_job(
        org_id=image_group.organization_id,
        user_id=PydanticObjectId(session.get("user_id")),
        product_id=image_group.product_id,
        prompt=body.prompt,
        count=1,
        image_group_ids=[image_group.id]
    )
    generation_job = await generation_job.insert()

    # Kick off the refinement process in the background
    asyncio.create_task(background_io_thread.run_async_task(
        background_refine_product_image,
        image_group.id,
        image.id,
        body.prompt,
        generation_job.id
    ))

    return {
        "generation_job_id": str(generation_job.id),
        "image_group_id": str(image_group.id),
        "image_id": str(image.id)
    }

@app.get("/api/generation/{generation_job_id}")
async def get_generation_job(generation_job_id: str):
    generation_job = await GenerationJob.get(generation_job_id)
    
    if generation_job.status == "error":
        error_message = generation_job.log[-1] if generation_job.log else "An error occurred during image generation"
        raise HTTPException(status_code=500, detail=error_message)
    
    response = {"generation_job": generation_job}
    
    if generation_job.status == "in_progress" or generation_job.status == "completed":
        # Fetch all image groups associated with this generation job
        image_groups = await GeneratedImageGroup.find(
            In(GeneratedImageGroup.id, generation_job.image_group_ids)
        ).to_list()
        
        response["image_groups"] = []
        
        for group in image_groups:
            # Fetch all images for each group
            generated_images = await GeneratedImage.find(
                GeneratedImage.group_id == group.id
            ).to_list()
            
            group_data = {
                "id": str(group.id),
                "created_at": group.created_at.isoformat(),
                "updated_at": group.updated_at.isoformat(),
                "images": [{"url": image.url, "status": image.status, "created_at": image.created_at.isoformat(), "id": str(image.id)} for image in generated_images]
            }
            response["image_groups"].append(group_data)
    
    return response

# Add a new endpoint to get image groups for a product
@app.get("/api/product/{product_id}/image-groups")
async def get_product_image_groups(product_id: str, session: dict = Depends(verify_session)):
    product = await Product.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    image_groups = await GeneratedImageGroup.find(
        GeneratedImageGroup.product_id == product.id,
        GeneratedImageGroup.deleted == None
    ).to_list()
    
    response = []
    for group in image_groups:
        images = await GeneratedImage.find(GeneratedImage.group_id == group.id).to_list()
        response.append({
            "id": str(group.id),
            "created_at": group.created_at.isoformat(),
            "updated_at": group.updated_at.isoformat(),
            "images": [{"url": image.url, "created_at": image.created_at.isoformat(), "id": str(image.id)} for image in images]
        })
    
    return {"image_groups": response}

@app.delete("/api/product/{product_id}/image-group/{group_id}")
async def delete_image_group(product_id: str, group_id: str, session: dict = Depends(verify_session)):
    product = await Product.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    image_group = await GeneratedImageGroup.get(group_id)
    if not image_group:
        raise HTTPException(status_code=404, detail="Image group not found")
    
    if image_group.product_id != product.id:
        raise HTTPException(status_code=403, detail="Image group does not belong to this product")
    
    await image_group.mark_as_deleted(session["user_id"])
    
    return {"message": "Image group deleted successfully"}

# Ensure the 'assets' directory exists
assets_dir = "assets"
if not os.path.exists(assets_dir):
    os.makedirs(assets_dir)
    print(f"Created directory: {assets_dir}")
else:
    print(f"Directory already exists: {assets_dir}")


@app.get("/auth")
async def auth(request: Request):
    # Get the base URL from the request
    base_url = str(request.base_url).rstrip('/')
    redirect_uri = f"{base_url}/api/hooks/workos"

    authorization_url = workos_client.user_management.get_authorization_url(
        provider="authkit",
        redirect_uri=redirect_uri
    )

    return RedirectResponse(url=authorization_url)

@app.get("/api/auth/status")
async def auth_status(request: Request, session: dict = Depends(verify_session)):
    try:
        user_id = session.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Validate the user exists
        user = await User.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get the user's organizations & update the db.
        org_memberships = await workos_client.user_management.list_organization_memberships(
            user_id=user.workos_id
        )

        orgs = []
        for org_membership in org_memberships.data:
            # Fetch the organization from WorkOS
            organization = await workos_client.organizations.get_organization(
                organization_id=org_membership.organization_id
            )
            existing_org = await Organization.find_one(Organization.workos_id == organization.id)
            if not existing_org:
                org = Organization.from_workos(organization.model_dump())
                await org.save()
            else:
                org = existing_org

            existing_membership = await OrganizationMembership.find_one(
                OrganizationMembership.user_id == user.id,
                OrganizationMembership.organization_id == org.id
            )
            if not existing_membership:
                org_membership = OrganizationMembership.from_workos(org_membership.model_dump(), user, org)
                await org_membership.save()
            else:
                await existing_membership.update_from_workos(org_membership.model_dump(), org, user)
            orgs.append({"id": str(org.id), "name": org.name})

        return {"status": "authenticated", "organizations": orgs}
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/api/hooks/workos")
async def callback(request: Request):
    # The authorization code returned by AuthKit
    code = request.query_params.get("code")

    if not code:
        raise HTTPException(status_code=400, detail="No code provided")

    try:
        auth_response = await workos_client.user_management.authenticate_with_code(
            code=code
        )

        # Check if the user already exists in the database
        existing_user = await User.find_one(User.workos_id == auth_response.user.id)
        
        if existing_user:
            user = existing_user
            # Update user information if needed
            await user.update_from_workos(auth_response.user.model_dump())
        else:
            # Create and insert new user
            user = User.from_workos(auth_response.user.model_dump())
            await user.insert()

        # Fetch and store organization memberships
        org_memberships = await workos_client.user_management.list_organization_memberships(
            user_id=auth_response.user.id
        )

        for org_membership in org_memberships.data:
            # Fetch the organization from WorkOS
            organization = await workos_client.organizations.get_organization(
                organization_id=org_membership.organization_id
            )
            
            # Check if the organization exists, create if not
            existing_org = await Organization.find_one(Organization.workos_id == organization.id)
            if existing_org:
                await existing_org.update_from_workos(organization.model_dump())
            else:
                existing_org = Organization.from_workos(organization.model_dump())
                await existing_org.insert()

            # Create or update organization membership
            existing_membership = await OrganizationMembership.find_one(
                OrganizationMembership.user_id == user.id,
                OrganizationMembership.organization_id == existing_org.id
            )
            if existing_membership:
                await existing_membership.update_from_workos(org_membership.model_dump(), existing_org, user)
            else:
                new_membership = OrganizationMembership.from_workos(org_membership.model_dump(), user, existing_org)
                await new_membership.insert()

        # Create the redirect response
        redirect = RedirectResponse(url="/app", status_code=302)

        # Set session cookie with last_refreshed timestamp
        session_data = {
            "user_id": str(user.id),  # Convert to string
            "access_token": auth_response.access_token,
            "refresh_token": auth_response.refresh_token,
            "last_refreshed": time.time()
        }
        redirect.set_cookie(
            key="session",
            value=json.dumps(session_data),
            httponly=True,
            # secure=True,
            samesite="lax",
            max_age=172800  # 2 days
        )

        # Return the response with the cookie set
        return redirect
    except Exception as e:
        # Handle any errors that might occur during authentication
        raise HTTPException(status_code=500, detail=str(e))

class WaitlistRequest(BaseModel):
    email: str

@app.post("/api/waitlist")
async def join_waitlist(request: WaitlistRequest):
    try:
        entry = WaitlistEntry(email=request.email)
        await entry.insert()
        return {"message": "Successfully joined the waitlist"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/image/{image_id}/download")
async def download_image(request: Request, image_id: str, session: dict = Depends(verify_session)):
    image = await GeneratedImage.get(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Extract blob name from the URL
    parsed_url = urlparse(image.url)
    blob_name = os.path.basename(parsed_url.path)

    print(blob_name) 
    # Fetch the image data from the blob storage
    blob_storage = request.state.toolbox.services.blob_storage
    blob_data = await blob_storage.download_blob(blob_name)
    
    # Create a streaming response
    return StreamingResponse(
        io.BytesIO(blob_data),
        media_type="image/jpeg",
        headers={
            "Content-Disposition": f"attachment; filename=generated_image_{image_id}.jpg"
        }
    )

#############################################################################
## KEEP THESE AT THE BOTTOM OF THE FILE. PUT EVERYTHING ELSE ABOVE HERE!!! ##
#############################################################################

app.mount("/api/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = f"../frontend/dist/{full_path}"
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse("../frontend/dist/index.html")

app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="react")
