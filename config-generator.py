from InquirerPy import inquirer
import json
from importlib import import_module
from rich.console import Console
from rich.tree import Tree

ROUTE_METADATA_OPTIONS = {
    "get": {
        "singular_response": {
            "description": "Only return a single item (400 if multiple)",
            "type": bool,
            "mandatory": False
        }
    },
    "post": {
        "creates_entry": {
            "description": "Whether to store the posted entry",
            "type": bool,
            "mandatory": False
        },
        "creates_created_at": {
            "description": "Auto add `created_at` timestamp",
            "type": bool,
            "mandatory": False
        },
        "creates_updated_at": {
            "description": "Auto add `updated_at` (set to None)",
            "type": bool,
            "mandatory": False
        },
    },
    "delete": {
        "singular_response": {
            "description": "Require exactly one item to delete",
            "type": bool,
            "mandatory": False
        }
    },
    "put": {}
}

console = Console()


def main():
    """
    Entry point of the application.
    Loads middleware modules, prompts user for middleware and route configurations,
    then saves the full configuration to a JSON file and prints it.
    """
    middleware_files = [
        "auth_token.py",
        "input_check.py",
        "permissions_token.py",
    ]

    print("Loading middleware...")
    available_middleware = load_middleware_modules(middleware_files)

    # Prompt config for each middleware
    for mw_name, mw_info in available_middleware.items():
        print(f"\nConfigure middleware: {mw_name}")
        config = prompt_required_config(
            mw_info.get("config_requirements", {}))
        mw_info["config"] = config  # save actual config

    routes = []
    while True:
        display_routes_tree(routes)
        add_route = inquirer.confirm(message="Add another route?").execute()
        if not add_route:
            break
        route = prompt_route_config(available_middleware)
        routes.append(route)

    full_config = {
        "middleware": {k: v["config"] for k, v in available_middleware.items()},
        "routes": routes,
    }

    # Save to JSON
    with open("config.json", "w") as f:
        json.dump(full_config, f, indent=2)

    print("\nConfig saved to config.json")
    console.print_json(json.dumps(full_config, indent=2))


def load_middleware_modules(middleware_files):
    """
    Dynamically imports middleware modules from given filenames.
    Expects each middleware module to provide `get_config_requirements` and `get_metadata_requirements` functions.

    Args:
        middleware_files (list[str]): List of middleware Python filenames.

    Returns:
        dict: Mapping of middleware module names to their config and metadata requirements.
    """
    available_middleware = {}
    for filename in middleware_files:
        # Assuming middleware files are Python modules named like 'auth_token.py'
        module_name = filename.replace('.py', '')
        module = import_module(f"middleware.{module_name}")
        # Expect each middleware module to expose a get_config_requirements() function returning a dict
        config_requirements = module.get_config_requirements()
        metadata_requirements = module.get_metadata_requirements()
        available_middleware[module_name] = {
            "config_requirements": config_requirements,
            "metadata_requirements": metadata_requirements
        }
    return available_middleware


def display_routes_tree(routes):
    """
    Displays a hierarchical tree of the configured routes, including their HTTP methods,
    endpoints, data sets, and any associated middleware and metadata.

    Args:
        routes (list[dict]): List of configured route dictionaries.
    """
    tree = Tree("Routes Configuration")

    if not routes:
        tree.add("[italic grey]No routes added yet[/]")
    else:
        for idx, route in enumerate(routes, start=1):
            route_branch = tree.add(
                f"[bold]{idx}. {route['method']} {route['endpoint']}[/]")
            route_branch.add(f"Data set: {route['data_set']}")
            middleware_branch = route_branch.add("Middleware:")
            if not route['middleware']:
                middleware_branch.add("[italic grey]None[/]")
            else:
                for mw in route['middleware']:
                    mw_metadata = route.get('metadata', {}).get(mw, {})
                    mw_text = f"{mw} - Metadata: {mw_metadata}" if mw_metadata else mw
                    middleware_branch.add(mw_text)

    console.print(tree)


def get_metadata_schema_for_route(method: str) -> dict:
    """
    Retrieves the metadata schema dictionary for a given HTTP method,
    based on predefined route metadata options.

    Args:
        method (str): HTTP method (e.g., 'GET', 'POST').

    Returns:
        dict: Metadata requirements for the specified HTTP method.
    """
    return ROUTE_METADATA_OPTIONS.get(method.lower(), {})


def prompt_route_config(available_middleware: dict) -> dict:
    """
    Prompts the user to configure a single route, including HTTP method, endpoint,
    data set name, middleware selection, and associated metadata for middleware and route.

    Args:
        available_middleware (dict): Middleware info including metadata requirements.

    Returns:
        dict: The fully configured route dictionary.
    """
    route = {}

    route['method'] = inquirer.select(
        message="Select HTTP method:",
        choices=["GET", "POST", "PUT", "DELETE"],
    ).execute()

    route['endpoint'] = inquirer.text(
        message="Enter endpoint (e.g. /api/users/:id):"
    ).execute()

    route['data_set'] = inquirer.text(
        message="Enter data set name:"
    ).execute()

    # Middleware multi-select
    middleware_choices = list(available_middleware.keys())
    selected_middleware = inquirer.checkbox(
        message="Select middleware to apply (space to toggle, enter to continue):",
        choices=middleware_choices,
    ).execute()

    route['middleware'] = selected_middleware
    route_md_requirements = get_metadata_schema_for_route(route['method'])

    def prompt_metadata():
        metadata = {}

        # Prompt metadata per middleware
        for mw_name in selected_middleware:
            mw_requirements = available_middleware[mw_name].get(
                'metadata_requirements', {})
            if mw_requirements:
                print(f"Configure metadata for middleware '{mw_name}':")
                mw_metadata = prompt_required_config(mw_requirements)
                metadata.update(mw_metadata)

        # Prompt route-level metadata
        md_metadata = prompt_required_config(route_md_requirements)
        metadata.update(md_metadata)

        return metadata

    route['metadata'] = prompt_metadata()

    return route


def prompt_required_config(requirements: dict) -> dict:
    """
    Generic prompt function for collecting configuration values based on given requirements.
    Supports types: bool (yes/no), dict (key-value pairs), list (comma-separated), int, float, and str.
    Validates mandatory fields and casts input to expected types.

    Args:
        requirements (dict): Mapping of field names to dicts describing description, type, and mandatory flag.

    Returns:
        dict: User input answers matching the requirements structure.
    """
    answers = {}

    for field, info in requirements.items():
        desc = info.get("description", "")
        mandatory = info.get("mandatory", False)
        field_type = info.get("type", str)  # default to str

        message = f"{field} {'(mandatory)' if mandatory else '(optional)'}: {desc}"

        # Handle boolean with confirm
        if field_type == bool:
            answer = inquirer.confirm(message=message).execute()

        elif field_type == dict:
            print(
                f"\nEnter key-value pairs for '{field}' (press enter to finish):")
            kv_pairs = {}
            while True:
                key = inquirer.text(
                    message="Key (leave blank to stop):").execute()
                if key.strip() == "":
                    break
                value = inquirer.text(message=f"Value for '{key}':").execute()
                kv_pairs[key] = value
            answer = kv_pairs

        else:
            answer = inquirer.text(
                message=message,
                validate=lambda val: val != "" if mandatory else True,
            ).execute()

            # Type cast (simple and naive — can be extended)
            if field_type == int:
                try:
                    answer = int(answer)
                except ValueError:
                    print(f"Invalid input. Expected an integer for '{field}'")
                    continue
            elif field_type == float:
                try:
                    answer = float(answer)
                except ValueError:
                    print(f"Invalid input. Expected a float for '{field}'")
                    continue
            elif field_type == list:
                answer = [item.strip()
                          for item in answer.split(",") if item.strip()]

        if answer or mandatory:
            answers[field] = answer

    return answers


if __name__ == "__main__":
    main()
