from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn
import collection_utils
import importlib
import uuid
from datetime import datetime, timezone

class JsonServer:
    """
    A class to dynamically create RESTful JSON API endpoints on a FastAPI app,
    with support for middleware, in-memory data storage, and customizable metadata.

    Attributes:
        app (FastAPI): The FastAPI application instance to which routes will be added.
        data (dict): In-memory storage for datasets managed by the server.
        middleware_config (dict): Configuration dictionary for middleware behavior and tokens.
    """
    def __init__(self, app: FastAPI):
        """
        Initializes the JsonServer with a FastAPI app instance.

        Args:
            app (FastAPI): The FastAPI application where the routes will be registered.
        """
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

    def add_get_route(self, endpoint: str, data_set: str, middleware: list[str], metadata: dict = None):
        """
        Adds a GET route to the FastAPI app that serves filtered data from the specified dataset.

        Args:
            endpoint (str): The URL path for the GET endpoint.
            data_set (str): The key of the dataset in self.data to query.
            middleware (list[str]): List of middleware names to run before handling the request.
            metadata (dict, optional): Additional options for route behavior (e.g., singular_response).

        Behavior:
            - Validates the existence of the dataset.
            - Runs middleware in order; if any returns a response, it short-circuits.
            - Filters dataset items by path and query parameters.
            - Returns a single entry if `singular_response` is True and exactly one match found.
            - Returns multiple matching entries otherwise.
            - Returns appropriate error responses if dataset not found, no matches, or multiple matches found for singular.
        """
        async def handler(request: Request):
            metadata = metadata or {}
            if data_set not in self.data:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"dataset {data_set} not found"}
                )
            for middleware_name in middleware:
                response = await self.run_middleware(middleware_name, request, metadata)
                if response:
                    return response
            path_params = request.path_params
            query_params = request.query_params
            filtered = collection_utils.filter_dict(self.data[data_set], {**path_params, **query_params})
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

    def add_post_route(self, endpoint:str, data_set: str, middleware:list[str], metadata: dict = None):
        """
        Adds a POST route to the FastAPI app for creating new entries in the specified dataset.

        Args:
            endpoint (str): The URL path for the POST endpoint.
            data_set (str): The key of the dataset in self.data to which new entries will be added.
            middleware (list[str]): List of middleware names to run before handling the request.
            metadata (dict, optional): Options affecting entry creation, such as auto-generating UUID, timestamps.

        Behavior:
            - Validates the existence of the dataset.
            - Runs middleware before processing.
            - Parses JSON request body.
            - Optionally adds UUID, created_at, updated_at fields based on metadata flags.
            - Adds the new entry to the dataset if 'creates_entry' is True.
            - Returns the created entry or success message accordingly.
        """
        async def handler(request: Request):
            metadata = metadata or {}
            if data_set not in self.data:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"dataset {data_set} not found"}
                )
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
                self.data[data_set].append(body)
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
    
    def add_delete_route(self, endpoint:str, data_set: str, middleware:list[str], metadata: dict = None):
        """
        Adds a DELETE route to remove entries from the specified dataset.

        Args:
            endpoint (str): The URL path for the DELETE endpoint.
            data_set (str): The key of the dataset in self.data from which entries will be deleted.
            middleware (list[str]): List of middleware names to run before handling the request.
            metadata (dict, optional): Options such as 'singular_response' to enforce deleting exactly one entry.

        Behavior:
            - Validates dataset existence.
            - Runs middleware checks.
            - Requires path or query parameters to identify entries to delete.
            - Filters entries matching parameters.
            - Enforces singular entry deletion if specified.
            - Removes matching entries from the dataset.
            - Returns deleted entries or errors accordingly.
        """
        async def handler(request: Request):
            metadata = metadata or {}
            if data_set not in self.data:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"dataset {data_set} not found"}
                )
            for middleware_name in middleware:
                response = await self.run_middleware(middleware_name, request, metadata)
                if response:
                    return response
            path_params = request.path_params
            query_params = request.query_params
            if not path_params and not query_params:
                return JSONResponse(
                    status_code=500,
                    content={"error": "DELETE route requires path or query parameters to locate entry"}
                )
            to_delete = collection_utils.filter_dict(self.data[data_set], {**path_params, **query_params})
            if not to_delete:
                return JSONResponse(
                    status_code=404,
                    content={"error": "No matching entries found to delete"}
                )
            if metadata.get("singular_response") and len(to_delete)!=1:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"{len(to_delete)} entries found, this endpoint expects a single entry to be found."}
                )
            # Actually remove matching items
            self.data[data_set] = [
                item for item in self.data[data_set] if item not in to_delete
            ]
            return JSONResponse(
                status_code=200,
                content=to_delete[0] if metadata.get("singular_response") else to_delete
            )
        self.app.delete(endpoint)(handler)
        
    def add_put_route(self, endpoint:str, data_set: str, middleware:list[str], metadata: dict = None):
        """
        Adds a PUT route to update an existing entry in the specified dataset.

        Args:
            endpoint (str): The URL path for the PUT endpoint.
            data_set (str): The key of the dataset in self.data containing entries to update.
            middleware (list[str]): List of middleware names to run before handling the request.
            metadata (dict, optional): Additional route behavior metadata.

        Behavior:
            - Validates dataset existence.
            - Runs middleware before processing.
            - Requires path or query parameters to locate the entry to update.
            - Accepts JSON body with update data.
            - Enforces exactly one matching entry.
            - Clears and updates the entry with new data.
            - Returns the updated entry or relevant errors.
        """
        async def handler(request: Request):
            metadata = metadata or {}
            if data_set not in self.data:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"dataset {data_set} not found"}
                )
            for middleware_name in middleware:
                response = await self.run_middleware(middleware_name, request, metadata)
                if response:
                    return response
            body = await request.json()
            if not body:
                return JSONResponse(
                    status_code=400,
                    content={"error": "No body provided"}
                )
            path_params = request.path_params
            query_params = request.query_params
            if not path_params and not query_params:
                return JSONResponse(
                    status_code=400,
                    content={"error": "PUT route requires path or query parameters to locate entry"}
                )
            to_update = collection_utils.filter_dict(self.data[data_set], {**path_params, **query_params})
            if not to_update:
                return JSONResponse(
                    status_code=404,
                    content={"error": "No matching entry found to update"}
                )
            if len(to_update)!=1:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"{len(to_update)} entries found, this endpoint expects a single entry to be found."}
                )
            # Actually update matching item
            to_update[0].clear()
            to_update[0].update(body)
            return JSONResponse(
                status_code=200,
                content=to_update[0]
            )
        self.app.put(endpoint)(handler)
        
    async def run_middleware(self, name: str, request: Request, metadata: dict):
        """
        Executes the specified middleware module on the given request.

        Args:
            name (str): The name of the middleware module to run (expected in middleware package).
            request (Request): The FastAPI request object.
            metadata (dict): Additional route behavior metadata.

        Returns:
            Response or None: Middleware response if it blocks the request, or None to continue.
        """
        mod = importlib.import_module(f"middleware.{name}")
        response = await mod.run(request, self.middleware_config[name], metadata)
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