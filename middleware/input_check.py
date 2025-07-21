from fastapi.responses import JSONResponse

async def run(request, config, metadata):
    """
    Middleware function to simulate input validation checks.

    Args:
        request (Request): The incoming FastAPI request object.
        config (dict): Configuration for this middleware, expected keys:
            - "flag_driven" (bool): Whether to simulate failure based on a flag.
            - "fail_next" (bool): If True, forces this middleware to return a failure response once.
        metadata (dict): Additional route-specific metadata (unused here).

    Returns:
        JSONResponse or None: Returns a 400 error response if `fail_next` is set,
        otherwise None to continue processing.
    """
    if config.get("flag_driven") and config.get("fail_next"):
        config["fail_next"] = False
        return JSONResponse(status_code=400, content={"error": "Simulated input validation failure"})
    return None