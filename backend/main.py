# Run with: uvicorn main:app --reload
import os
import json 
from datetime import datetime, timezone
from typing import List

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from workos import AsyncWorkOSClient

from models import Organization, OrganizationMembership, Product, User, init_beanie_models
from middleware.session import SessionMiddleware
from background_jobs.train_product_lora import train_product_lora
import background_jobs.background_io_thread as background_io_thread

load_dotenv()

REDIRECT_URI = os.getenv("WORKOS_REDIRECT_URI", "http://localhost:8000/api/hooks/workos")
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

app = FastAPI()

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

@app.get("/api/product")
async def get_products(request: Request, organization_id: str = None, session: dict = Depends(verify_session)):
    user_id = session.get("user_id")
    
    # If no organization_id is provided, get the default organization for the user
    if not organization_id:
        user = await User.get(user_id)
        organization_id = user.default_organization_id
    
    # Fetch products for the specified organization
    products = await Product.find(Product.organization_id == organization_id).to_list()
    
    return {"products": products}

class CreateProductRequest(BaseModel):
    name: str
    primary_image_id: str
    primary_image_url: str
    additional_image_ids: List[str] = Field(default_factory=list)
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
        organization_id=user.organization_id,
        created_by_user_id=user_id,
        primary_image_id=request.primary_image_id,
        primary_image_url=request.primary_image_url,
        additional_image_ids=request.additional_image_ids,
        additional_image_urls=request.additional_image_urls,
        model_id=None  # This will be set during the training process
    )
    
    # Kick off the training process in the background
    background_io_thread.run_async_task(train_product_lora, product)
    
    return {"product": product}

# Ensure the 'assets' directory exists
assets_dir = "assets"
if not os.path.exists(assets_dir):
    os.makedirs(assets_dir)
    print(f"Created directory: {assets_dir}")
else:
    print(f"Directory already exists: {assets_dir}")


@app.get("/auth")
async def auth():
    authorization_url = workos_client.user_management.get_authorization_url(
        provider="authkit",
        redirect_uri=REDIRECT_URI
    )

    return RedirectResponse(url=authorization_url)

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
                OrganizationMembership.user_id == str(user.id),
                OrganizationMembership.organization_id == str(existing_org.id)
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
            "last_refreshed": datetime.now(timezone.utc).isoformat()
        }
        redirect.set_cookie(
            key="session",
            value=json.dumps(session_data),
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=3600  # 1 hour, adjust as needed
        )

        # Return the response with the cookie set
        return redirect
    except Exception as e:
        # Handle any errors that might occur during authentication
        raise HTTPException(status_code=500, detail=str(e))



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