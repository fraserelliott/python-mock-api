def strict_filter_dict(data: list[dict], filters: dict) -> list[dict]:
    filtered = []
    for item in data:
        if all(item.get(k) == v for k, v in filters.items()):
            filtered.append(item)
    return filtered

def filter_dict(data: list[dict], filters: dict) -> list[dict]:
    filtered = []
    for item in data:
        if all(str(item.get(k)) == v for k, v in filters.items()):
            filtered.append(item)
    return filtered