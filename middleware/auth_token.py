from fastapi.responses import JSONResponse
from fastapi import Request
from typing import Optional, List
from pydantic import BaseModel, ValidationError


class AuthTokenConfig(BaseModel):
    accepted_token: str
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
            content={
                "error": "Missing required config key for auth_token middleware: 'accepted_token'"}
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
        AuthTokenConfig(**config)
        return None
    except ValidationError as e:
        return e.errors()


def validate_metadata(metadata: dict) -> Optional[dict]:
    """
    Function used in parsing to validate that the required metadata has been provided. This is required to be in all middleware.

    Args:
        metadata (dict): Additional route-specific metadata (unused here).

    Returns:
        None if metadata provided is sufficient or a dict explaining which metadata is missing or malformed.
    """
    return None


def get_config_requirements() -> dict:
    """
    Function used in wizards to generate the server config. This signature is shared among all middleware and is required by all middleware.

    Returns:
        A dict explaining requirements.
    """
    return {
        "accepted_token":
            {
                "description": "A single string for the token this middleware should accept as authenticated for all routes.",
                "mandatory": True,
                "type": str
            },
            "flag_driven":
            {
                "description": "A bool to say whether the server can trigger a fail_next flag for this route to return error 403 on the next request.",
                "mandatory": False,
                "type": bool
            }
    }


def get_metadata_requirements() -> dict:
    """
      Function used in wizards to generate the server config. This signature is shared among all middleware and is required by all middleware.

      Returns:
          A dict explaining requirements.
    """
    return {}
