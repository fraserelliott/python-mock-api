from fastapi.responses import JSONResponse

async def run(request, config):
    if "accepted_token" not in config:
        return JSONResponse(status_code=500, content={"error": "Missing required config key for auth_token middleware: 'accepted_token"})
    
    auth_header = request.headers.get("Authorization")
    accepted_token = config["accepted_token"]
    if config.get("flag_driven") and config.get("fail_next"):
        config["fail_next"] = False
        return JSONResponse(status_code=403, content={"error": "Simulated auth failure"})

    if auth_header != f"Bearer {accepted_token}":
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    return None