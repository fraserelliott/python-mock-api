from fastapi.responses import JSONResponse

async def run(request, config, metadata):
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