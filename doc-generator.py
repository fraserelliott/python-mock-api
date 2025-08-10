import json

config = dict()
datasets = dict()


def print_value(input) -> str:
    if isinstance(input, list):
        middle = ", ".join([item for item in input])
        return "[ " + middle + " ]"
    if isinstance(input, dict):
        if not input:
            return "(none)"
        indented_list = [f"  - {key}: {value}" for key, value in input.items()]
        return "\n" + "\n".join(indented_list)
    return str(input)


def list_dict(input: dict) -> str:
    items = [f"- {key}: {print_value(value)}" for key, value in input.items()]
    return "\n".join(items)


def list_dict_exclude_keys(input: dict, exclude_keys: set) -> str:
    filtered = {k: v for k, v in input.items() if k not in exclude_keys}
    return list_dict(filtered)


def load_data():
    global config, datasets
    with open("config.json", "r") as f:
        config = json.load(f)
    for endpoint in config.get("routes", []):
        dataset_name = endpoint.get("data_set")
        if dataset_name and dataset_name not in datasets:
            with open(f"{dataset_name}.json") as dataset:
                datasets[dataset_name] = json.load(dataset)


def generate_middleware_notes() -> str:
    global config
    mw_notes = []
    for name, mw_config in config.get("middleware", {}).items():
        mw_cfg_notes = list_dict(mw_config)
        mw_cfg_note = f"### {name}\n" + mw_cfg_notes
        mw_notes.append(mw_cfg_note)
    return "## Middleware\n\n" + "\n\n".join(mw_notes)


def generate_dataset_notes() -> str:
    global datasets
    dataset_notes = []
    for name, dataset in datasets.items():
        ds_fields = [f"{key}" for key in dataset[0]]
        ds_note = f"### {name}\n" + ", ".join(ds_fields)
        fk_warning = generate_foreign_key_warnings(name)
        if fk_warning:
            ds_note += "\n\n" + fk_warning
        dataset_notes.append(ds_note)
    return "## Datasets\n\n" + "\n\n".join(dataset_notes)


def generate_foreign_key_warnings(dataset_name):
    try:
        with open(f"{dataset_name}-config.json") as f:
            schema = json.load(f)
    except FileNotFoundError:
        return ""

    warning_lines = []

    if "linked_to" in schema:
        warning_lines.append(
            f"**Note:** This dataset is linked to `{schema['linked_to']}` via `{schema['linked_to']}_id` foreign key field.")

    fields = schema.get("fields", {})
    foreign_keys = [field for field, spec in fields.items(
    ) if spec.get("type") == "foreign_key"]
    if not foreign_keys and not warning_lines:
        return ""

    if foreign_keys:
        warning_lines.append(
            "**Note:** The following fields are foreign keys and should not be used to trigger extra fetches:")
        for fk in foreign_keys:
            warning_lines.append(f"- `{fk}`")

    return "\n".join(warning_lines)


def generate_endpoint_notes() -> str:
    global config
    endpoint_notes = []
    for route in config.get("routes", []):
        endpoint = route.get("endpoint", "")
        route_notes = list_dict_exclude_keys(route, {"endpoint"})
        route_note = f"### {endpoint}\n" + route_notes
        endpoint_notes.append(route_note)
    return "## Endpoints\n\n" + "\n\n".join(endpoint_notes)


def main():
    with open("template.md", "r") as f:
        template = f.read()

    # Generate your sections
    middleware_notes = generate_middleware_notes()
    dataset_notes = generate_dataset_notes()
    endpoint_notes = generate_endpoint_notes()

    # Combine everything - you can append the generated notes after the template
    output = template + "\n\n" + middleware_notes + \
        "\n\n" + dataset_notes + "\n\n" + endpoint_notes

    with open("output.md", "w") as f:
        f.write(output)


if __name__ == "__main__":
    load_data()
    main()
