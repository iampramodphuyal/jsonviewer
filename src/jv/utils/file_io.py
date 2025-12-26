"""File and stdin input handling for jv."""

import json
import sys
from pathlib import Path
from typing import Any


def read_json_input(file_path: Path | None = None) -> tuple[Any, str, str]:
    """
    Read JSON from file or stdin.

    Returns:
        tuple: (parsed_data, source_name, raw_content)

    Raises:
        ValueError: If no input is provided or JSON is invalid.
    """
    if file_path is not None:
        content = file_path.read_text(encoding="utf-8")
        source = str(file_path)
    elif not sys.stdin.isatty():
        content = sys.stdin.read()
        source = "stdin"
    else:
        raise ValueError("No input provided. Provide a file path or pipe JSON to stdin.")

    try:
        data = json.loads(content)
        return data, source, content
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON at line {e.lineno}, column {e.colno}: {e.msg}")


def format_json(data: Any, indent: int = 2) -> str:
    """Pretty-print JSON data."""
    return json.dumps(data, indent=indent, ensure_ascii=False)


def minify_json(data: Any) -> str:
    """Minify JSON data."""
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)
