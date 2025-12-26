"""JSONPath utilities for jv."""

from typing import Any


def get_jsonpath(keys: list[str | int]) -> str:
    """
    Convert a list of keys to JSONPath notation.

    Args:
        keys: List of keys/indices representing the path.

    Returns:
        JSONPath string (e.g., "$.users[0].name")
    """
    if not keys:
        return "$"

    path = "$"
    for key in keys:
        if isinstance(key, int):
            path += f"[{key}]"
        elif "." in str(key) or " " in str(key) or not str(key).isidentifier():
            # Quote keys with special characters
            escaped = str(key).replace('"', '\\"')
            path += f'["{escaped}"]'
        else:
            path += f".{key}"

    return path


def get_value_at_path(data: Any, keys: list[str | int]) -> Any:
    """
    Get value at a specific path in JSON data.

    Args:
        data: The JSON data structure.
        keys: List of keys/indices representing the path.

    Returns:
        The value at the specified path.

    Raises:
        KeyError: If path doesn't exist.
    """
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current[str(key)]
        elif isinstance(current, list):
            current = current[int(key)]
        else:
            raise KeyError(f"Cannot index into {type(current).__name__}")
    return current
