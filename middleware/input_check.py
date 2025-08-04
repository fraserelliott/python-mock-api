from fastapi.responses import JSONResponse
from fastapi import Request
from typing import Optional

#todo: config validation for flag_driven
#todo: change fail_next to metadata

async def run(request: Request, config: dict, metadata: dict) -> Optional[JSONResponse]:
    """
    Middleware function to simulate input validation checks.

    Args:
        request (Request): The incoming FastAPI request object.
        config (dict): Configuration for this middleware, expected keys:
            - "flag_driven" (bool): Whether to simulate failure based on a flag.
        metadata (dict): Additional route-specific metadata (unused here).
            - "fail_next" (bool): If True, forces this middleware to return a failure response once.

    Returns:
        JSONResponse or None: Returns a 400 error response if `fail_next` is set,
        otherwise None to continue processing.
    """
    if config.get("flag_driven") and metadata.get("fail_next"):
        metadata["fail_next"] = False
        return JSONResponse(status_code=400, content={"error": "Simulated input validation failure"})
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
    return None