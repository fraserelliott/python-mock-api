from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn
import collection_utils
import importlib

class JsonServer:
    def __init__(self, app: FastAPI):
        self.app = app
        self.data = dict()
        self.middleware_config = {
            "auth_token": {
                "accepted_token": "validtoken123",
                "flag_driven": True,
                "fail_next": False
            },
            "input_check": {
                "flag_driven": True,
                "fail_next": False
            }
        }

    def add_get_route(self, endpoint: str, data: list[dict], middleware: list[str], singular_response: bool):
        async def handler(request: Request):            
            path_params = request.path_params
            query_params = request.query_params
            filtered = data
            
            for middleware_name in middleware:
                response = await self.run_middleware(middleware_name, request)
                if response:
                    return response
            
            if path_params:
                filtered = collection_utils.filter_dict(filtered, path_params)
            if query_params:
                filtered = collection_utils.filter_dict(filtered, query_params)
            
            if not filtered:
                return JSONResponse(
                    status_code=404,
                    content={"error": "Item not found"}
                )
                
            if singular_response and len(filtered)==1:
                return JSONResponse(
                    status_code=200,
                    content={"data":filtered[0]}
                )
            elif singular_response:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"{len(filtered)} entries found, this endpoint expects a single entry to be found."}
                )    
            return JSONResponse(
                status_code=200,
                content={"data": filtered}
            )
        self.app.get(endpoint)(handler)
        
    async def run_middleware(self, name, request):
        mod = importlib.import_module(f"middleware.{name}")
        response = await mod.run(request, self.middleware_config[name])
        return response

app = FastAPI()
server = JsonServer(app)
server.add_get_route("/hello/{id}", [{"id": 4, "message": "Hello World!"}], ["auth_token"], False)

if __name__ == "__main__":
    uvicorn.run(
        "server:app",             # refers to `app` in `server.py`
        host="127.0.0.1",
        port=8000,
        ssl_keyfile="./ssl/key.pem",  # SSL private key
        ssl_certfile="./ssl/cert.pem" # SSL certificate
    )