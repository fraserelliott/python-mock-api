from InquirerPy import inquirer
import json
from importlib import import_module
from rich.console import Console
from rich.tree import Tree

# TODO: route metadata dict

console = Console()

def main():
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
        config = prompt_middleware_config(
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


def prompt_route_config(available_middleware: dict) -> dict:
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
    middleware_choices = list(available_middleware.keys()) + ["<none>"]
    selected_middleware = inquirer.checkbox(
        message="Select middleware to apply (space to toggle, enter to continue):",
        choices=middleware_choices,
    ).execute()

    # Remove the placeholder "<none>" if it's selected
    if "<none>" in selected_middleware:
        selected_middleware = []
        
    route['middleware'] = selected_middleware

    # Now prompt metadata per middleware
    metadata = {}
    for mw_name in selected_middleware:
        mw_requirements = available_middleware[mw_name].get(
            'metadata_requirements', {})
        if mw_requirements:
            print(f"Configure metadata for middleware '{mw_name}':")
            mw_metadata = prompt_middleware_config(mw_requirements)
            metadata[mw_name] = mw_metadata

    route['metadata'] = metadata

    return route


def prompt_middleware_config(requirements: dict) -> dict:
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
