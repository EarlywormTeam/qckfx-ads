from fastapi import Request, HTTPException, Response
from fastapi.middleware import Middleware
import time
from joserfc import jwt
from joserfc.jwk import KeySet
import json
import requests
from workos import AsyncWorkOSClient

class SessionMiddleware(Middleware):
    def __init__(self, workos: AsyncWorkOSClient, cookie_password: str):
        self.workos = workos
        self.cookie_password = cookie_password
        jwks = workos.user_management.get_jwks_url()
        r = requests.get(jwks)
        self.keyset = KeySet.import_key_set(r.json())

    async def dispatch(self, request: Request, call_next):
        session_cookie = request.cookies.get("session")
        if not session_cookie:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        session = json.loads(session_cookie)
        if session:
            try:
                access_token = session.get("access_token")
                claims_requests = jwt.JWTClaimsRegistry()
                claims = jwt.decode(access_token, self.keyset).claims
                claims_requests.validate(claims)
            except Exception as e:
                print("Error:", e)
                raise HTTPException(status_code=401, detail="Invalid session")
            
            try:
                access_token_exp = claims.get("exp")
                # Other stuff on claims here: https://workos.com/docs/reference/user-management/session-tokens/access-token

                if access_token_exp and access_token_exp > time.time():
                    request.state.session = {
                        "authenticated": True,
                        "user_id": session.get("user_id"),
                        "session_id": claims.get("sid"),
                        "organization_id": claims.get("org_id"),
                        "role": claims.get("role"),
                        "permissions": claims.get("permissions")
                    }
                else:
                    raise HTTPException(status_code=401, detail="Session expired")
                
                
                response: Response = call_next(request)

                # Check if we need to refresh the session (e.g., once a day)
                last_refreshed = float(session.get("last_refreshed", 0))
                if not last_refreshed or (time.time() - last_refreshed) > 86400:
                    try:
                        refresh_result = await self.workos.user_management.authenticate_with_refresh_token(
                            refresh_token=session.get("refresh_token")
                        )
                        claims = jwt.decode(refresh_result["access_token"], self.keyset).claims
                        claims_requests.validate(claims)
                    except Exception as e:
                        print("Error:", e)
                        raise HTTPException(status_code=401, detail="Session authentication failed")
                    
                    session_data = session | {
                        "access_token": refresh_result["access_token"],
                        "refresh_token": refresh_result["refresh_token"],
                        "last_refreshed": time.time()
                    }

                    response.set_cookie(
                        key="session",
                        value=session_data,
                        httponly=True,
                        secure=True,
                        samesite="lax",
                        max_age=172800  # 2 days
                    )
                
                return response
            except Exception as e:
                print("Error:", e)
                raise HTTPException(status_code=401, detail="Session authentication failed")
        else:
            request.state.session = None
        
        return call_next(request)
