def strict_filter_dict(data: list[dict], filters: dict) -> list[dict]:
    return [
        item for item in data
        if all(item.get(k) == v for k, v in filters.items())
    ]

def filter_dict(data: list[dict], filters: dict) -> list[dict]:
    return [
        item for item in data
        if all(str(item.get(k)) == str(v) for k, v in filters.items())
    ]