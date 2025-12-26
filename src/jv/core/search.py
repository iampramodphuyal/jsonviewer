"""Search functionality for jv."""

from dataclasses import dataclass
from typing import Any, Generator


@dataclass
class SearchResult:
    """Represents a search match in the JSON tree."""

    path: list[str | int]
    key: str | int | None
    value: Any
    match_in_key: bool
    match_in_value: bool


def search_json(
    data: Any,
    query: str,
    path: list[str | int] | None = None,
    case_sensitive: bool = False,
) -> Generator[SearchResult, None, None]:
    """
    Search JSON recursively for matching keys/values.

    Args:
        data: The JSON data to search.
        query: The search string.
        path: Current path in the tree (internal use).
        case_sensitive: Whether to match case.

    Yields:
        SearchResult objects for each match.
    """
    if path is None:
        path = []

    if not query:
        return

    def matches(text: str) -> bool:
        if case_sensitive:
            return query in text
        return query.lower() in text.lower()

    if isinstance(data, dict):
        for key, value in data.items():
            current_path = path + [key]
            key_matches = matches(str(key))
            value_matches = isinstance(value, str) and matches(value)

            if key_matches or value_matches:
                yield SearchResult(
                    path=current_path,
                    key=key,
                    value=value,
                    match_in_key=key_matches,
                    match_in_value=value_matches,
                )

            # Recurse into nested structures
            if isinstance(value, (dict, list)):
                yield from search_json(value, query, current_path, case_sensitive)
            elif isinstance(value, str) and matches(value) and not key_matches:
                # Already yielded above if key matched
                pass

    elif isinstance(data, list):
        for idx, item in enumerate(data):
            current_path = path + [idx]

            if isinstance(item, str) and matches(item):
                yield SearchResult(
                    path=current_path,
                    key=idx,
                    value=item,
                    match_in_key=False,
                    match_in_value=True,
                )
            elif isinstance(item, (dict, list)):
                yield from search_json(item, query, current_path, case_sensitive)

    elif isinstance(data, str) and matches(data):
        yield SearchResult(
            path=path,
            key=None,
            value=data,
            match_in_key=False,
            match_in_value=True,
        )


def count_matches(data: Any, query: str, case_sensitive: bool = False) -> int:
    """Count total matches in JSON data."""
    return sum(1 for _ in search_json(data, query, case_sensitive=case_sensitive))
