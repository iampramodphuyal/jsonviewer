# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Installation

```bash
# Setup environment
cd /Users/pramodphuyal/Documents/projects/jsonviewer
uv venv && source .venv/bin/activate
uv pip install -e ".[all]"      # Install with all optional dependencies
```

### Global Access (add to ~/.zshrc)

```bash
# Add alias for jv command
echo 'alias jv="source /Users/pramodphuyal/Documents/projects/jsonviewer/.venv/bin/activate && jv"' >> ~/.zshrc
source ~/.zshrc
```

Or add this function for cleaner usage:
```bash
cat >> ~/.zshrc << 'EOF'
jv() {
    /Users/pramodphuyal/Documents/projects/jsonviewer/.venv/bin/python -m jv "$@"
}
EOF
source ~/.zshrc
```

## Build & Development Commands

```bash
# Setup environment (if not using alias)
source .venv/bin/activate
uv pip install -e ".[dev]"      # Install with dev dependencies

# Run the CLI
jv file.json                    # Terminal TUI
jv file.json -w                 # Browser mode
cat file.json | jv              # Stdin

# Linting
ruff check src/
ruff format src/

# Type checking
mypy src/jv

# Testing
pytest                          # Run all tests
pytest tests/test_cli.py        # Run specific test file
pytest -k "test_name"           # Run specific test
```

## Architecture

This is a Python CLI tool (`jv`) for viewing JSON files with two viewing modes:

### Entry Points
- `src/jv/cli.py` - Typer CLI definition, handles all command-line arguments and dispatches to TUI or web mode
- `src/jv/__main__.py` - Enables `python -m jv`

### Core Modules (`src/jv/core/`)
- `search.py` - Recursive JSON search returning `SearchResult` objects with paths
- `path.py` - JSONPath utilities (`get_jsonpath()`, `get_value_at_path()`)

### Terminal UI (`src/jv/tui/`)
Built with Textual framework:
- `app.py` - `JSONViewerApp` main application with keybindings, search handling, theme toggle
- `widgets/json_tree.py` - `JSONTree` widget extending Textual's Tree with JSON-specific rendering, type icons, fold/unfold
- `widgets/search_bar.py` - `SearchBar` widget with live search and result navigation
- `styles/app.tcss` - Textual CSS styles

### Web Mode (`src/jv/web/`)
- `server.py` - HTTP server that embeds JSON into an HTML template with JavaScript tree viewer (Catppuccin themed)

### Utilities (`src/jv/utils/`)
- `file_io.py` - `read_json_input()` handles file and stdin, `format_json()`, `minify_json()`
- `clipboard.py` - Cross-platform clipboard with pyperclip fallback to pbcopy/wl-copy/xclip

## Key Patterns

- JSON data flows: `cli.py` reads via `file_io.py` → passes to `run_tui()` or `run_web_viewer()`
- Tree nodes store `{"path": [...], "value": ...}` in their `data` attribute for JSONPath construction
- Search results are `SearchResult` dataclass with `path`, `key`, `value`, `match_in_key`, `match_in_value`
- Optional dependencies (jmespath, jsonschema) are imported lazily in cli.py with user-friendly error messages
