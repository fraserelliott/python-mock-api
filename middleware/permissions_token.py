from fastapi.responses import JSONResponse

async def run(request, config, metadata):
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