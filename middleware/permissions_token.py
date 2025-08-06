from fastapi.responses import JSONResponse
from fastapi import Request
from typing import Optional, List, Dict
from pydantic import BaseModel, ValidationError


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
            content={
                "error": "Missing required config key for permissions_token middleware: 'accepted_tokens'"}
        ), False
    if "accepted_roles" not in metadata:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Missing required metadata key for permissions_token middleware: 'accepted_roles'"}
        ), False
    if metadata.get("fail_next"):
        return JSONResponse(
            status_code=403,
            content={"error": "Simulated auth failure"}
        ), True
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return JSONResponse(
            status_code=401,
            content={"error": "Missing Authorization header"}
        ), False
    accepted_tokens = config["accepted_tokens"]
    accepted_roles = metadata["accepted_roles"]
    for role in accepted_roles:
        if role in accepted_tokens and auth_header == f"Bearer {accepted_tokens[role]}":
            return None, False  # Provided token matches user permission required
    return JSONResponse(
        status_code=401,
        content={"error": "Unauthorized"}
    ), False


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


def get_config_requirements() -> dict:
    """
    Function used in wizards to generate the server config. This signature is shared among all middleware and is required by all middleware.

    Returns:
        A dict explaining requirements.
    """
    return {
        "accepted_tokens":
            {
                "description": "A dict for the tokens this middleware should associate to given roles.",
                "mandatory": True,
                "type": dict
            },
    }


def get_metadata_requirements() -> dict:
    """
      Function used in wizards to generate the server config. This signature is shared among all middleware and is required by all middleware.

      Returns:
          A dict explaining requirements.
    """
    return {
        "accepted_roles":
        {
            "description": " list of roles that should be accepted for the route.",
            "mandatory": True,
            "type": list
        }
    }
