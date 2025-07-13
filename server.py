from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import collection_utils

class JsonServer:
    def __init__(self, app: FastAPI):
        self.app = app

    def add_get_route(self, endpoint: str, data: list[dict], singular_response: bool):
        async def handler(request: Request):
            path_params = request.path_params
            query_params = request.query_params
            filtered = data
            
            if path_params:
                filtered = collection_utils.strict_filter_dict(filtered, path_params)
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

app = FastAPI()
server = JsonServer(app)
server.add_get_route("/hello/{id}", {"message": "Hello World!"}, False)

if __name__ == "__main__":
    uvicorn.run(
        "server:app",             # refers to `app` in `server.py`
        host="127.0.0.1",
        port=8000,
        ssl_keyfile="./ssl/key.pem",  # your SSL private key
        ssl_certfile="./ssl/cert.pem" # your SSL certificate
    )