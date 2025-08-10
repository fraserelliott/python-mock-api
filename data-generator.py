import json
import os
from InquirerPy import inquirer
import uuid
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('en_gb')


def generate_foreign_key(options: dict) -> str:
    dataset_name = options.get("dataset")
    if not dataset_name:
        raise ValueError("foreign_key generator requires a 'dataset' option")

    # Load dataset once and cache it for performance if needed
    # For simplicity, load fresh each time here:
    try:
        with open(f"{dataset_name}.json") as f:
            dataset = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Dataset file '{dataset_name}.json' not found")

    # Pick a random record's id
    if not dataset:
        raise ValueError(f"Dataset '{dataset_name}' is empty")

    return random.choice(dataset)["id"]

def generate_avatar(options: dict) -> str:
    seed = generate_uuid(None)
    size = options.get("size", 100)
    return f"https://i.pravatar.cc/{size}?u={seed}"


def generate_image(options: dict) -> str:
    seed = generate_uuid(None)
    width = options.get("width", 100)
    height = options.get("height", 100)
    return f"https://picsum.photos/seed/{seed}/{width}/{height}"


def generate_dog_image(options: dict) -> str:
    width = options.get("width", 100)
    height = options.get("height", width)
    return f"https://place.dog/{width}/{height}"


def generate_street(options: dict) -> str:
    return fake.street_address()


def generate_city(options: dict) -> str:
    return fake.city()


def generate_postcode(options: dict) -> str:
    return fake.postcode()


def generate_company(options: dict) -> str:
    return fake.company()


def generate_url(options: dict) -> str:
    return fake.url()


def generate_password(options: dict) -> str:
    min_length = options.get("min_length", 8)
    max_length = options.get("max_length", 16)
    length = random.randint(min_length, max_length)
    special_chars = options.get("use_special_chars", True)
    return fake.password(length=length, special_chars=special_chars)


def generate_integer(options: dict) -> int:
    min = options.get("min", 0)
    max = options.get("max", 100)
    return random.randint(min, max)


def generate_price(options: dict) -> float:
    min = options.get("min", 1)
    max = options.get("max", 1000)
    price = random.uniform(min, max)
    return round(price, 2)


def generate_uuid(options: dict) -> str:
    return str(uuid.uuid4())


def generate_name(options: dict) -> str:
    return fake.name()


def generate_email(options: dict) -> str:
    return fake.email()


def generate_lorem(options: dict) -> str:
    length = options.get("char_length", 100)
    return fake.text(max_nb_chars=length)


def generate_phone(options: dict) -> str:
    char_length = options.get("char_length", 11)
    prefix = options.get("prefix", "0")
    remaining_len = char_length - len(prefix)
    if remaining_len <= 0:
        return prefix[:char_length]
    remaining_digits = ''.join(random.choices('0123456789', k=remaining_len))
    return prefix + remaining_digits


def generate_datetime_utc(options: dict) -> str:
    # Extract start and end components with defaults
    start_year = options.get("start_year", 2000)
    start_month = options.get("start_month", 1)
    start_day = options.get("start_day", 1)

    end_year = options.get("end_year", 2025)
    end_month = options.get("end_month", 12)
    end_day = options.get("end_day", 31)

    start_date = datetime(start_year, start_month, start_day)
    end_date = datetime(end_year, end_month, end_day)

    # Compute total seconds range
    delta_seconds = int((end_date - start_date).total_seconds())
    random_seconds = random.randint(0, delta_seconds)

    random_datetime = start_date + timedelta(seconds=random_seconds)
    # Return ISO 8601 UTC string with 'Z' suffix
    return random_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")


def load_schema(data_set_name, prompt_usage=False):
    schema_file = f"{data_set_name}-config.json"
    if os.path.exists(schema_file):
        if prompt_usage:
            use_existing = inquirer.confirm(
                message=f"A config for '{data_set_name}' exists. Regenerate using the same schema?"
            ).execute()
        else:
            use_existing = True
        if use_existing:
            with open(schema_file) as f:
                return json.load(f)
    return None


def save_schema(data_set_name, fields, linked_to=None):
    full_schema = {}
    if linked_to:
        full_schema["linked_to"] = linked_to
    full_schema["fields"] = fields
    with open(f"{data_set_name}-config.json", "w") as f:
        json.dump(full_schema, f, indent=2)


def save_generated_data(data_set_name, data):
    with open(f"{data_set_name}.json", "w") as f:
        json.dump(data, f, indent=2)


def ensure_id_field(fields: dict) -> dict:
    if "id" not in fields:
        fields = {"id": {"type": "uuid"}, **fields}
    return fields


def generate_dataset_from_schema(schema: dict, count: int) -> list:
    return [generate_entry(schema, idx) for idx in range(1, count + 1)]


GEN_FIELDS = {
    "street": {
        "func": generate_street,
        "options": {},
        "description": "A realistic street name"
    },
    "city": {
        "func": generate_city,
        "options": {},
        "description": "A realistic city name"
    },
    "postcode": {
        "func": generate_postcode,
        "options": {},
        "description": "A realistic UK postcode"
    },
    "company": {
        "func": generate_company,
        "options": {},
        "description": "A fake company or brand name"
    },
    "url": {
        "func": generate_url,
        "options": {},
        "description": "A realistic-looking URL"
    },
    "password": {
        "func": generate_password,
        "options": {
            "min_length": {"type": int, "default": 8, "description": "Minimum password length"},
            "max_length": {"type": int, "default": 16, "description": "Maximum password length"},
            "use_special_chars": {"type": bool, "default": True, "description": "Include special characters"},
        },
        "description": "A random password with optional special characters"
    },
    "integer": {
        "func": generate_integer,
        "options": {
            "min": {"type": int, "default": 0, "description": "Minimum integer value"},
            "max": {"type": int, "default": 100, "description": "Maximum integer value"},
        },
        "description": "A random integer within a given range"
    },
    "price": {
        "func": generate_price,
        "options": {
            "min": {"type": float, "default": 0.0, "description": "Minimum price"},
            "max": {"type": float, "default": 1000.0, "description": "Maximum price"},
            "currency_symbol": {"type": str, "default": "£", "description": "Currency symbol"},
        },
        "description": "A price with currency symbol between a range"
    },
    "uuid": {
        "func": generate_uuid,
        "options": {},
        "description": "A random UUID (universally unique identifier)"
    },
    "name": {
        "func": generate_name,
        "options": {},
        "description": "A realistic full name"
    },
    "email": {
        "func": generate_email,
        "options": {},
        "description": "A realistic email address"
    },
    "lorem": {
        "func": generate_lorem,
        "options": {
            "char_length": {"type": int, "default": 100, "description": "Max number of characters"},
        },
        "description": "Random filler text (Lorem Ipsum)"
    },
    "phone": {
        "func": generate_phone,
        "options": {
            "char_length": {"type": int, "default": 11, "description": "Phone number length"},
            "prefix": {"type": str, "default": "0", "description": "Phone number prefix"},
        },
        "description": "A phone number with custom prefix and length"
    },
    "date": {
        "func": generate_datetime_utc,
        "options": {
            "start_day": {"type": int, "default": 1, "description": "Start day"},
            "start_month": {"type": int, "default": 1, "description": "Start month"},
            "start_year": {"type": int, "default": 2000, "description": "Start year"},
            "end_day": {"type": int, "default": 31, "description": "End day"},
            "end_month": {"type": int, "default": 12, "description": "End month"},
            "end_year": {"type": int, "default": 2025, "description": "End year"},
        },
        "description": "A UTC datetime (ISO format) between two dates"
    },
    "avatar": {
        "func": generate_avatar,
        "options": {
            "size": {"type": int, "default": 100, "description": "The size of the square avatar link in pixels"}
        },
        "description": "An avatar link (pravatar)"
    },
    "image": {
        "func": generate_image,
        "options": {
            "width": {"type": int, "default": 100, "description": "Width (pixels)"},
            "height": {"type": int, "default": 100, "description": "Height (pixels)"},
        },
        "description": "An image link (picsum)"
    },
    "dog_image": {
        "func": generate_dog_image,
        "options": {
            "width": {"type": int, "default": 100, "description": "Width (pixels)"},
            "height": {"type": int, "default": 100, "description": "Height (pixels)"},
        },
        "description": "An image of a pet (loremflickr)"
    },
    "foreign_key": {
        "func": generate_foreign_key,
        "options": {
            "dataset": {"type": str, "default": "", "description": "The name of the dataset json file"}
        },
        "description": "The id field of a random entry in a specified dataset"
    }
}


def prompt_field_type() -> str:
    choices = [
        {"name": f"{key} — {val['description']}", "value": key}
        for key, val in GEN_FIELDS.items()
    ]

    return inquirer.select(
        message="What kind of data do you want to generate for this field?",
        choices=choices
    ).execute()


def prompt_options(field_type: str) -> dict:
    field = GEN_FIELDS.get(field_type, {})
    options_spec = field.get("options", {})
    answers = {}

    for key, spec in options_spec.items():
        default = spec.get("default")
        desc = spec.get("description", key)
        value_type = spec.get("type", str)

        answer = inquirer.text(
            message=f"{desc} [{default}]"
        ).execute()

        if answer == "":
            answers[key] = default
        else:
            try:
                answers[key] = value_type(answer)
            except ValueError:
                print(f"Invalid input for {key}, using default.")
                answers[key] = default

    return answers


def generate_entry(schema: dict, idx: int) -> dict:
    fields = schema.get("fields", {})
    entry = {}
    for field, spec in fields.items():
        field_type = spec.get("type")
        gen_func = GEN_FIELDS.get(field_type, {}).get("func")
        options = {
            **spec.get("options", {}),
            "index": idx
        }

        if gen_func:
            entry[field] = gen_func(options)
        else:
            entry[field] = None
    return entry


def generate_linked_dataset():
    # Get the new dataset name
    new_dataset_name = inquirer.text(
        message="Enter the new dataset name:").execute()
    
    # Load or generate schema for new linked dataset
    schema = load_schema(new_dataset_name, True)
    if not schema:
        fields = generate_fields()
        
        # Ask which dataset to link to
        linked_dataset_name = inquirer.text(
            message="Enter the parent dataset name for linking:").execute()
                
        save_schema(new_dataset_name, fields, linked_dataset_name)
        # Reload with correct structure
        schema = load_schema(new_dataset_name)
        
    new_data = []
    linked_dataset_name = schema.get("linked_to")
    
    linked_dataset_file = f"{linked_dataset_name}.json"

    # Load linked dataset records
    if not os.path.exists(linked_dataset_file):
        print(f"Linked dataset '{linked_dataset_file}' not found!")
        return

    with open(linked_dataset_file) as f:
        linked_records = json.load(f)

    # Set foreign key field name (e.g. posts_id)
    foreign_key_field = f"{linked_dataset_name}_id"
    print(f"Using foreign key field: '{foreign_key_field}'")
    
    # Get how many linked records per linked entry
    min_count = int(inquirer.text(
        message="Minimum number of linked records per parent?").execute())
    max_count = int(inquirer.text(
        message="Maximum number of linked records per parent?").execute())

    for parent_record in linked_records:
        linked_num = random.randint(min_count, max_count)
        parent_id = parent_record.get("id")
        for _ in range(linked_num):
            entry = generate_entry(schema, idx=0)
            entry[foreign_key_field] = parent_id
            new_data.append(entry)

    save_generated_data(new_dataset_name, new_data)
    print(f"\nSaved {len(new_data)} linked records to {new_dataset_name}.json")


def generate_dataset():
    data_set_name = inquirer.text(message="Enter data set name:").execute()
    schema = load_schema(data_set_name, True)

    if not schema:
        fields = generate_fields()
        save_schema(data_set_name, fields)
        # Reload with correct structure
        schema = load_schema(data_set_name)
        
    num_records = int(inquirer.text(
        message="How many records to generate?").execute())

    data = generate_dataset_from_schema(schema, num_records)

    save_generated_data(data_set_name, data)
    print(f"\nSaved {num_records} records to {data_set_name}.json")


def generate_fields():
    fields = {}
    while True:
        add_field = inquirer.confirm(message="Add another field?").execute()
        if not add_field:
            break
        name = inquirer.text(message="Enter field name:").execute()
        field_type = prompt_field_type()
        options = prompt_options(field_type)
        fields[name] = {"type": field_type, "options": options}
    fields = ensure_id_field(fields)
    return fields


if __name__ == "__main__":
    is_linked = inquirer.confirm(message="Generate a linked dataset?").execute()
    if is_linked:
        generate_linked_dataset()
    else:
        generate_dataset()
