from fastapi.responses import JSONResponse

async def run(request, config, metadata):
    """
    Middleware function to simulate validating presence and correctness of an authorization token.

    Args:
        request (Request): The incoming FastAPI request object.
        config (dict): Configuration with expected keys:
            - "accepted_token" (str): The valid token string to compare against.
            - "flag_driven" (bool): Enables simulation of failure if `fail_next` is True.
            - "fail_next" (bool): If True, forces a simulated failure once.
        metadata (dict): Additional route-specific metadata (unused here).

    Returns:
        JSONResponse or None: Returns HTTP 401 if no or invalid Authorization header,
        HTTP 403 if simulated failure triggered, HTTP 500 if misconfigured,
        otherwise None to continue processing.
    """
    if "accepted_token" not in config:
        return JSONResponse(
            status_code=500,
            content={"error": "Missing required config key for auth_token middleware: 'accepted_token"}
        )
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return JSONResponse(
            status_code=401,
            content={"error": "Missing Authorization header"}
        )
    accepted_token = config["accepted_token"]
    if config.get("flag_driven") and config.get("fail_next"):
        config["fail_next"] = False
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