from fastapi import Request, HTTPException
from fastapi.middleware import Middleware
from datetime import datetime, timedelta
from workos import AsyncWorkOSClient

class SessionMiddleware(Middleware):
    def __init__(self, workos: AsyncWorkOSClient, cookie_password: str):
        self.workos = workos
        self.cookie_password = cookie_password

    async def dispatch(self, request: Request, call_next):
        session_cookie = request.cookies.get("session")
        if session_cookie:
            try:
                auth_result = await self.workos.user_management.authenticate_with_session_cookie(
                    session_data=session_cookie,
                    cookie_password=self.cookie_password
                )
                
                if auth_result["authenticated"]:
                    request.state.session = auth_result
                    response = await call_next(request)

                    # Check if we need to refresh the session (e.g., once a day)
                    last_refreshed = auth_result.get("last_refreshed")
                    if not last_refreshed or (datetime.now() - last_refreshed) > timedelta(days=1):
                        refresh_result = await self.workos.user_management.refresh_and_seal_session_data(
                            session_data=session_cookie,
                            cookie_password=self.cookie_password
                        )
                        if refresh_result["authenticated"]:
                            response.set_cookie(
                                key="session",
                                value=refresh_result["sealed_session"],
                                httponly=True,
                                secure=True,
                                samesite="lax"
                            )
                    
                    return response
                else:
                    raise HTTPException(status_code=401, detail="Invalid session")
            except Exception as e:
                raise HTTPException(status_code=401, detail="Session authentication failed")
        else:
            request.state.session = None
        
        return await call_next(request)
