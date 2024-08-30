# Run with: uvicorn main:app --reload
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from workos import AsyncWorkOSClient

load_dotenv()

REDIRECT_URI = os.getenv("WORKOS_REDIRECT_URI")
workos_client = AsyncWorkOSClient(api_key=os.getenv("WORKOS_API_KEY"), client_id=os.getenv("WORKOS_CLIENT_ID"))

app = FastAPI()

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
        user = await workos_client.user_management.authenticate_with_code(
            code=code
        )

        # Use the information in `user` for further business logic.
        # For example, you might want to store the user in your database or set a session.

        # Redirect the user to the homepage
        return RedirectResponse(url="/app")
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