# Run with: uvicorn main:app --reload
import os
import json 

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from workos import AsyncWorkOSClient
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from models.user import User

load_dotenv()

REDIRECT_URI = os.getenv("WORKOS_REDIRECT_URI", "http://localhost:8000/api/hooks/workos")
workos_client = AsyncWorkOSClient(api_key=os.getenv("WORKOS_API_KEY"), client_id=os.getenv("WORKOS_CLIENT_ID"))

app = FastAPI()

async def init_db():
    # MongoDB connection string
    mongodb_url = os.getenv("MONGODB_URL")
    
    # Create Motor client
    client = AsyncIOMotorClient(mongodb_url)
    
    # Initialize Beanie with the Motor client and your document models
    # Replace `YourDocument1, YourDocument2` with your actual document models
    await init_beanie(database=client.qckfx, document_models=[User])

# Modify the startup event to initialize the database
@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/api/home")
async def root():
    return {"message": "Hello World"}

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

        # Create the redirect response
        redirect = RedirectResponse(url="/app", status_code=302)

        # Set session cookie
        session_data = {
            "user_id": str(user.id),  # Convert to string
            "access_token": auth_response.access_token,
            "refresh_token": auth_response.refresh_token
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