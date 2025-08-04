from fastapi.responses import JSONResponse
from fastapi import Request
from typing import Optional, List
from pydantic import BaseModel, ValidationError

#todo: config validation for flag_driven

class PermissionsTokenConfig(BaseModel):
    accepted_tokens: List[str]
    flag_driven: Optional[bool]

async def run(request: Request, config: dict, metadata: dict) -> Optional[JSONResponse]:
    """
    Middleware function to simulate validating presence and correctness of an authorization token. This is required to be in all middleware.

    Args:
        request (Request): The incoming FastAPI request object.
        config (dict): Configuration with expected keys:
            - "accepted_token" (str): The valid token string to compare against.
            - "flag_driven" (bool): Enables simulation of failure if `fail_next` is True.
        metadata (dict): Additional route-specific metadata:
            - "fail_next" (bool): If True, forces a simulated failure once. This should only be set by the server if flag_driven is True.

    Returns:
        JSONResponse or None: Returns HTTP 401 if no or invalid Authorization header,
        HTTP 403 if simulated failure triggered, HTTP 500 if misconfigured,
        otherwise None to continue processing.
    """
    if "accepted_token" not in config:
        return JSONResponse(
            status_code=500,
            content={"error": "Missing required config key for auth_token middleware: 'accepted_token'"}
        )
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return JSONResponse(
            status_code=401,
            content={"error": "Missing Authorization header"}
        )
    accepted_token = config["accepted_token"]
    if config.get("flag_driven") and metadata.get("fail_next"):
        metadata["fail_next"] = False
        return JSONResponse(
            status_code=403,
            content={"error": "Simulated auth failure"}
        )
    if auth_header != f"Bearer {accepted_token}":
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized"}
        )
    return None

def validate_metadata(metadata: dict) -> Optional[dict]:
    """
    Function used in parsing to validate that the required metadata has been provided. This is required to be in all middleware.
    
    Args:
        metadata (dict): Additional route-specific metadata (unused here).
    
    Returns:
        None if metadata provided is sufficient or a dict explaining which metadata is missing or malformed.
    """
    return None

def get_requirements() -> Optional[dict]:
    """
    Function used in wizards to generate the server config. This is shared among all middleware. This is required to be in all middleware.
    
    Returns:
        None if no config options or metadata are required or a dict explaining config options and metadata requirements. e.g.
        {
            "config": { "accepted_tokens": "A dict mapping each user role to tokens that the middleware should accept for that role."},
            "metadata": { "accepted_roles": "A list of roles that should be accepted for the route."}
        }
    """
    return { "config": { "accepted_token": "A single string for the token this middleware should accept as authenticated for all routes.",
             "flag_driven": "A bool to say whether the server can trigger a fail_next flag for this route to return error 500 on the next request."} }