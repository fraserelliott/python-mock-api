from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn
import collection_utils
import importlib
import uuid
from datetime import datetime, timezone

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
            },
            "permissions_token": {
                "accepted_tokens": {
                    "admin": "admintoken123",
                    "user": "usertoken123"
                },
                "flag_driven": True,
                "fail_next": False
            }
        }

    # todo: refactor data to string
    def add_get_route(self, endpoint: str, data: list[dict], middleware: list[str], metadata: dict = None):
        async def handler(request: Request):
            metadata = metadata or {}
            
            for middleware_name in middleware:
                response = await self.run_middleware(middleware_name, request, metadata)
                if response:
                    return response
                
            path_params = request.path_params
            query_params = request.query_params
            filtered = data
            if path_params:
                filtered = collection_utils.filter_dict(filtered, path_params)
            if query_params:
                filtered = collection_utils.filter_dict(filtered, query_params)
            
            if not filtered:
                return JSONResponse(
                    status_code=404,
                    content={"error": "Item not found"}
                )
                
            if metadata.get("singular_response"):
                if len(filtered)==1:
                    return JSONResponse(
                        status_code=200,
                        content=filtered[0]
                    )
                else:
                    return JSONResponse(
                        status_code=400,
                        content={"error": f"{len(filtered)} entries found, this endpoint expects a single entry to be found."}
                    )    
            return JSONResponse(
                status_code=200,
                content={"data": filtered}
            )
        self.app.get(endpoint)(handler)

    def add_post_route(self, endpoint:str, data: list[dict], middleware:list[str], metadata: dict = None):
        async def handler(request: Request):
            metadata = metadata or {}
            for middleware_name in middleware:
                response = await self.run_middleware(middleware_name, request, metadata)
                if response:
                    return response
            body = await request.json()
            if metadata.get("creates_uuid"):
                body["uuid"] = str(uuid.uuid4())
            if metadata.get("creates_created_at"):
                body["created_at"] = datetime.now(timezone.utc).isoformat()
            if metadata.get("creates_updated_at"):
                body["updated_at"] = None
            if metadata.get("creates_entry"):
                data.append(body)
                return JSONResponse(
                    status_code=200,
                    content=body
                    )
            else:
                return JSONResponse(
                    status_code=200,
                    content={"message": "Successful post, no entries created" }
                )
        self.app.post(endpoint)(handler)
    
    # todo: refactor data to string
    def add_delete_route(self, endpoint:str, data: list[dict], middleware:list[str], metadata: dict = None):
        async def handler(request: Request):
            metadata = metadata or {}
            for middleware_name in middleware:
                response = await self.run_middleware(middleware_name, request, metadata)
                if response:
                    return response
            path_params = request.path_params
            query_params = request.query_params
            if not path_params and not query_params:
                return JSONResponse(
                    status_code=500,
                    content={"error": "Delete route needs to include path or query params to find the entry"}
                )
            filtered = data
            if path_params:
                filtered = collection_utils.filter_dict(filtered, path_params)
            if query_params:
                filtered = collection_utils.filter_dict(filtered, query_params)
            if metadata.get("singular_response"):
                if len(filtered)==1:
                    entry = filtered[0]
                    
                    return JSONResponse(
                        status_code=200,
                        content=filtered[0]
                    )
                else:
                    return JSONResponse(
                        status_code=400,
                        content={"error": f"{len(filtered)} entries found, this endpoint expects a single entry to be found."}
                    )    
            return JSONResponse(
                status_code=200,
                content={"data": filtered}
            )
            
    async def run_middleware(self, name, request):
        mod = importlib.import_module(f"middleware.{name}")
        response = await mod.run(request, self.middleware_config[name])
        return response

app = FastAPI()
server = JsonServer(app)
server.add_get_route("/hello/{id}", [{"id": 4, "message": "Hello World!"}], ["auth_token"], {"singular_response": True})

if __name__ == "__main__":
    uvicorn.run(
        "server:app",             # refers to `app` in `server.py`
        host="127.0.0.1",
        port=8000,
        ssl_keyfile="./ssl/key.pem",  # SSL private key
        ssl_certfile="./ssl/cert.pem" # SSL certificate
    )