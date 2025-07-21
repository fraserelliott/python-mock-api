def strict_filter_dict(data: list[dict], filters: dict) -> list[dict]:
    """
    Filters a list of dictionaries, returning only those where each key matches the filter value exactly,
    including type and value.

    Args:
        data (list[dict]): The list of dictionaries to filter.
        filters (dict): Key-value pairs that each returned dictionary must match exactly.

    Returns:
        list[dict]: A list of dictionaries from `data` matching all the filters exactly.
    """
    return [
        item for item in data
        if all(item.get(k) == v for k, v in filters.items())
    ]

def filter_dict(data: list[dict], filters: dict) -> list[dict]:
    """
    Filters a list of dictionaries, returning those where each key matches the filter value after
    converting both values to strings (loose equality).

    Args:
        data (list[dict]): The list of dictionaries to filter.
        filters (dict): Key-value pairs that each returned dictionary must match loosely (string equality).

    Returns:
        list[dict]: A list of dictionaries from `data` matching all the filters after string conversion.
    """
    return [
        item for item in data
        if all(str(item.get(k)) == str(v) for k, v in filters.items())
    ]