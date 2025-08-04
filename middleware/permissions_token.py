from fastapi.responses import JSONResponse
from fastapi import Request
from typing import Optional, List, Dict
from pydantic import BaseModel, ValidationError

#todo: config validation for flag_driven
#todo: change fail_next to metadata

class PermissionsTokenMetadata(BaseModel):
    accepted_roles: List[str]
    
class PermissionsTokenConfig(BaseModel):
    accepted_tokens: Dict[str, str]

async def run(request: Request, config: dict, metadata: dict) -> Optional[JSONResponse]:
    """
    Middleware function to simulate validating authorization token against accepted roles and tokens.

    Args:
        request (Request): The incoming FastAPI request object.
        config (dict): Configuration with expected key:
            - "accepted_tokens" (dict): Maps roles to their valid tokens.
        metadata (dict): Metadata must include:
            - "accepted_roles" (list[str]): Roles allowed to access the route.

    Returns:
        JSONResponse or None: Returns HTTP 401 if missing or unauthorized token,
        HTTP 500 if configuration or metadata is missing,
        otherwise None if the token matches an accepted role.
    """
    if "accepted_tokens" not in config:
        return JSONResponse(
            status_code=500,
            content={"error": "Missing required config key for permissions_token middleware: 'accepted_tokens'"}
        )
    if "accepted_roles" not in metadata:
        return JSONResponse(
            status_code=500,
            content={"error": "Missing required metadata key for permissions_token middleware: 'accepted_roles'"}
        )
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return JSONResponse(
            status_code=401,
            content={"error": "Missing Authorization header"}
        )
    accepted_tokens = config["accepted_tokens"]
    accepted_roles = metadata["accepted_roles"]
    for role in accepted_roles:
        if role in accepted_tokens and auth_header == f"Bearer {accepted_tokens[role]}":
            return None # Provided token matches user permission required
    return JSONResponse(
        status_code=401,
        content={"error": "Unauthorized"}
    )

def validate_metadata(metadata: dict) -> Optional[dict]:
    """
    Function used in parsing to validate that the required metadata has been provided.
    This is required to be in all middleware modules to ensure the provided metadata is correct.
    
    Args:
        metadata (dict): Additional route-specific metadata. Must include "accepted_roles".
    
    Returns:
        None if metadata provided is sufficient or a dict explaining which metadata is missing or malformed.
    """
    try:
        PermissionsTokenMetadata(**metadata)
        return None
    except ValidationError as e:
        return e.errors()

def validate_config(config: dict) -> Optional[list]:
    """
    Validates the middleware-specific configuration against its expected schema.
    This function is required in all middleware modules to ensure the provided config is correct.

    Args:
        config (dict): The configuration dictionary provided for the middleware.

    Returns:
        None if the config is valid, or a list of Pydantic validation errors if invalid.
        Each error is a dict describing the issue, including the field, message, and type.
    """
    try:
        PermissionsTokenConfig(**config)
        return None
    except ValidationError as e:
        return e.errors()

def get_requirements() -> Optional[dict]:
    """
    Function used in wizards to generate the server config. This is shared among all middleware.
    This is required to be in all middleware.
    
    Returns:
        None if no config options or metadata are required or a dict explaining config options and metadata requirements. e.g.
        {
            "config": { "accepted_tokens": "A dict mapping each user role to tokens that the middleware should accept for that role."},
            "metadata": { "accepted_roles": "A list of roles that should be accepted for the route."}
        }
    """
    return {
            "config": { "accepted_tokens": "A dict mapping each user role to tokens that the middleware should accept for that role."},
            "metadata": { "accepted_roles": "A list of roles that should be accepted for the route."}
            }