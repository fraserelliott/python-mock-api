from fastapi.responses import JSONResponse

async def run(request, config, metadata):    
    if config.get("flag_driven") and config.get("fail_next"):
        config["fail_next"] = False
        return JSONResponse(status_code=400, content={"error": "Simulated input validation failure"})
    return None