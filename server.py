from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Optional, Literal
import uvicorn
import utils.collection_utils as collection_utils
import importlib
import uuid
import json
import sys
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator, ValidationError
import os

# TODO: refactor metadata to store per route

class RouteConfig(BaseModel):
    endpoint: str
    data_set: str
    method: Literal["GET", "POST", "PUT", "DELETE"]
    middleware: Optional[list[str]] = None
    metadata: Optional[dict] = None

    @field_validator("middleware")
    @classmethod
    def validate_middleware(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        for middleware in v:
            # Check if file middleware.py exists
            file_path = os.path.join(os.getcwd(), "middleware", middleware + ".py")
            if not os.path.isfile(file_path):
                raise ValueError(
                    f"Invalid middleware: {middleware} does not exist at {file_path}")
        return v


class JsonServer:
    """
    A class to dynamically create RESTful JSON API endpoints on a FastAPI app,
    with support for middleware, in-memory data storage, and customizable metadata.

    Attributes:
        app (FastAPI): The FastAPI application instance to which routes will be added.
        data (dict): In-memory storage for datasets managed by the server.
        middleware_config (dict): Configuration dictionary for middleware behavior and tokens.
        middleware (dict): Dictionary of middleware loaded during config parsing
    """

    def __init__(self, app: FastAPI):
        """
        Initializes the JsonServer with a FastAPI app instance.

        Args:
            app (FastAPI): The FastAPI application where the routes will be registered.
        """
        self.app = app
        self.data = dict()
        self.middleware_config = dict()
        self.middleware = dict()
        self.fail_next = dict()
        self.routes = set()

    def add_get_route(self, endpoint: str, data_set: str, middleware: list[str] = None, metadata: dict = None):
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
        metadata = metadata or {}
        middleware = middleware or []
        async def handler(request: Request):
            if data_set not in self.data:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"dataset {data_set} not found"}
                )
            response = self.check_route_failure_flag("GET", endpoint)
            if response:
              return response
            for middleware_name in middleware:
                response = await self.run_middleware(middleware_name, request, metadata)
                if response:
                    return response
            path_params = request.path_params
            query_params = request.query_params
            filtered = collection_utils.filter_dict(
                self.data[data_set], {**path_params, **query_params})
            if not filtered:
                return JSONResponse(
                    status_code=404,
                    content={"error": "Item not found"}
                )
            if metadata.get("singular_response"):
                if len(filtered) == 1:
                    return JSONResponse(
                        status_code=200,
                        content=filtered[0]
                    )
                else:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": f"{len(filtered)} entries found, this endpoint expects a single entry to be found."}
                    )
            return JSONResponse(
                status_code=200,
                content={"data": filtered}
            )
        self.app.get(endpoint)(handler)

    def add_post_route(self, endpoint: str, data_set: str, middleware: list[str] = None, metadata: dict = None):
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
        metadata = metadata or {}
        middleware = middleware or []
        async def handler(request: Request):
            if data_set not in self.data:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"dataset {data_set} not found"}
                )
            response = self.check_route_failure_flag("POST", endpoint)
            if response:
              return response
            for middleware_name in middleware:
                response = await self.run_middleware(middleware_name, request, metadata)
                if response:
                    return response
            try:
                body = await request.json()
            except Exception:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid JSON body"}
                )

            if not body:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Request body is required"}
                )
            # Validation against dataset shape
            template = self.data[data_set][0] if self.data[data_set] else {}
            missing_fields = [k for k in template.keys() if k != 'id' and k not in body]

            if missing_fields:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": f"Missing required fields: {missing_fields}"}
                )
            body["id"] = str(uuid.uuid4())
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
                    content={"message": "Successful post, no entries created"}
                )
        self.app.post(endpoint)(handler)

    def add_delete_route(self, endpoint: str, data_set: str, middleware: list[str] = None, metadata: dict = None):
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
        metadata = metadata or {}
        middleware = middleware or []
        async def handler(request: Request):
            if data_set not in self.data:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"dataset {data_set} not found"}
                )
            response = self.check_route_failure_flag("DELETE", endpoint)
            if response:
              return response
            for middleware_name in middleware:
                response = await self.run_middleware(middleware_name, request, metadata)
                if response:
                    return response
            path_params = request.path_params
            query_params = request.query_params
            if not path_params and not query_params:
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "DELETE route requires path or query parameters to locate entry"}
                )
            to_delete = collection_utils.filter_dict(
                self.data[data_set], {**path_params, **query_params})
            if not to_delete:
                return JSONResponse(
                    status_code=404,
                    content={"error": "No matching entries found to delete"}
                )
            if metadata.get("singular_response") and len(to_delete) != 1:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": f"{len(to_delete)} entries found, this endpoint expects a single entry to be found."}
                )
            # Actually remove matching items
            to_delete_ids = {item['id'] for item in to_delete}

            self.data[data_set] = [
                item for item in self.data[data_set] if item.get('id') not in to_delete_ids
            ]

            return JSONResponse(
                status_code=200,
                content=to_delete[0] if metadata.get(
                    "singular_response") else to_delete
            )
        self.app.delete(endpoint)(handler)

    def add_put_route(self, endpoint: str, data_set: str, middleware: list[str] = None, metadata: dict = None):
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
        metadata = metadata or {}
        middleware = middleware or []
        async def handler(request: Request):
            if data_set not in self.data:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"dataset {data_set} not found"}
                )
            response = self.check_route_failure_flag("PUT", endpoint)
            if response:
              return response
            for middleware_name in middleware:
                response = await self.run_middleware(middleware_name, request, metadata)
                if response:
                    return response
            try:
                body = await request.json()
            except Exception:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid JSON body"}
                )

            if not body:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Request body is required"}
                )
            path_params = request.path_params
            query_params = request.query_params
            if not path_params and not query_params:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "PUT route requires path or query parameters to locate entry"}
                )
            to_update = collection_utils.filter_dict(
                self.data[data_set], {**path_params, **query_params})
            if not to_update:
                return JSONResponse(
                    status_code=404,
                    content={"error": "No matching entry found to update"}
                )
            if len(to_update) != 1:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": f"{len(to_update)} entries found, this endpoint expects a single entry to be found."}
                )
            # Check shape of body matches the object stored (all keys except 'id')
            to_update_item = to_update[0]
            expected_fields = set(to_update_item.keys()) - {"id"}
            provided_fields = set(body.keys())
            missing_fields = expected_fields - provided_fields
            if missing_fields:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": f"Missing fields in request body: {', '.join(missing_fields)}"
                    }
                )
            # Actually update existing item
            existing_id = to_update_item.get("id")
            to_update_item.clear()
            to_update_item.update(body)
            to_update_item["id"] = existing_id
            return JSONResponse(
                status_code=200,
                content=to_update_item
            )
        self.app.put(endpoint)(handler)
    
    
    def check_route_failure_flag(self, method, endpoint):
      route_key = f"{method}:{endpoint}"
      if self.fail_next.get(route_key, False):
          # Respond with 500 error (simulated failure)
          self.fail_next[route_key] = False  # reset flag
          return JSONResponse(status_code=500, content={"error": "Simulated failure"})

    async def run_middleware(self, name: str, request: Request, metadata: dict):
        """
        Executes the specified middleware module on the given request.

        Args:
            name (str): The name of the middleware module to run from self.middleware.
            request (Request): The FastAPI request object.
            metadata (dict): Additional route behavior metadata.

        Returns:
            Response or None: Middleware response if it blocks the request, or None to continue.
        """
        metadata = dict(metadata)
        mod = self.middleware.get(name)
        if not mod:
            raise Exception(f"Middleware not found for {name}")
        config = self.middleware_config.get(name, {})
        # Inject fail_next flag into metadata, run middleware and clear flag if failure was simulated
        metadata["fail_next"] = self.fail_next.get(f"middleware:{name}", False)
        response, should_clear_flag = await mod.run(request, config, metadata)
        if should_clear_flag:
            self.fail_next[f"middleware:{name}"] = False
        return response

    def parse_config(self):
        """
        Loads and validates the route configuration from 'config.json'.

        This method reads a JSON config file, ensures it is a list of route definitions,
        validates each route using the RouteConfig Pydantic model, and registers each
        valid route with the appropriate HTTP method handler (GET, POST, PUT, DELETE).

        If the configuration file is malformed, missing required fields, or contains
        invalid data, the server will print an error message and exit with code 1.

        Raises:
            SystemExit: If the config file is not a list, is invalid JSON, or contains
                        route definitions that fail validation.
        """
        try:
            with open("config.json", "r") as file:
                raw_config = json.load(file)
        except json.JSONDecodeError as e:
            print(f"Malformed config.json: {e}")
            sys.exit(1)
        # verify correct structure
        if not isinstance(raw_config, dict):
            print("Config must be a dict with a list of route definitions and a dict for middleware configuration.")
            sys.exit(1)
        try:
            self.middleware_config = raw_config.get("middleware", {})
            errors = self.load_middleware()
            if errors:
                print(f"Invalid middleware config: {errors}")
                sys.exit(1)
            route_config = raw_config.get("routes", [])
            routes = [RouteConfig(**route) for route in route_config]
            for route in routes:
                self.routes.add(f"{route.method}:{route.endpoint}")
                routefuncs = {
                    "GET": self.add_get_route,
                    "POST": self.add_post_route,
                    "PUT": self.add_put_route,
                    "DELETE": self.add_delete_route}
                routefuncs[route.method](
                    route.endpoint, route.data_set, route.middleware, route.metadata)
                self.ensure_dataset_loaded(route.data_set)
        except ValidationError as e:
            print(f"Config validation error:\n{e}")

    def load_seed_data(self, filepath: str):
        try:
            with open(filepath, "r") as f:
                seed_data = json.load(f)
            if not isinstance(seed_data, list):
                raise ValueError(
                    f"Seed file {filepath} does not contain a list")
            print(f"Loaded seed data from {filepath}")
            return seed_data
        except Exception as e:
            print(f"Failed to load seed data from {filepath}: {e}")
            return []

    def load_middleware(self):
        errors = {}
        for key, conf in self.middleware_config.items():
            if key not in self.middleware:
                try:
                    self.middleware[key] = importlib.import_module(f"middleware.{key}")
                except ModuleNotFoundError:
                    errors[key] = [f"Module '{key}.py' not found."]
                    continue
                try:
                    validation_errors = self.middleware[key].validate_config(
                        conf)
                    if validation_errors:  # If not None, it’s a list of errors
                        errors[key] = validation_errors
                except AttributeError:
                    errors[key] = [
                        f"'validate_config' function not found in '{key}.py'."]
                except Exception as e:
                    errors[key] = [f"Error validating {key}: {str(e)}"]

    def ensure_dataset_loaded(self, data_set: str):
        if data_set not in self.data:
            data = self.load_seed_data(f"{data_set}.json")

            if not isinstance(data, list):
                raise ValueError(f"Dataset {data_set} must be a list")

            ids = set()
            for idx, item in enumerate(data):
                if not isinstance(item, dict):
                    raise ValueError(
                        f"Item at index {idx} in dataset {data_set} is not an object")
                unique_id = item.get("id")
                if not unique_id:
                    raise ValueError(
                        f"Item at index {idx} in dataset {data_set} lacks 'id'")
                if unique_id in ids:
                    raise ValueError(
                        f"Duplicate id '{unique_id}' found in dataset {data_set}")
                ids.add(unique_id)

            self.data[data_set] = data

    def reset_datasets(self):
        """
        Reloads all previously loaded datasets from their corresponding JSON files,
        effectively resetting them to their original seed state.
        """
        loaded_keys = list(self.data.keys())
        self.data.clear()
        for key in loaded_keys:
            self.ensure_dataset_loaded(key)
        print(f"Reset datasets: {loaded_keys}")

app = FastAPI()
server = JsonServer(app)
server.parse_config()

if __name__ == "__main__":
    uvicorn.run(
        "server:app",             # refers to `app` in `server.py`
        host="127.0.0.1",
        port=8000,
    )