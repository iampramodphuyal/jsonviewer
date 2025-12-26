# jv - JSON Viewer

A powerful CLI tool for viewing and navigating JSON files in terminal or browser.

## Features

- **Terminal TUI**: Interactive tree view with fold/unfold, vim-style navigation
- **Browser Mode**: Opens JSON in a local web-based viewer with search and navigation
- **Search**: Find keys and values with live highlighting and navigation
- **JSONPath**: Copy path to any node for use in code
- **JMESPath Queries**: Filter and extract data using JMESPath expressions
- **Validation**: Validate JSON syntax and against JSON Schema
- **Diff**: Compare two JSON files and show differences
- **Themes**: Dark and light color schemes
- **Stdin Support**: Pipe JSON from any command

## Installation

```bash
# Clone and install with uv
git clone https://github.com/iampramodphuyal/jv.git
cd jv
uv venv && source .venv/bin/activate
uv pip install -e ".[all]"

# Or install specific extras
uv pip install -e "."              # Core only
uv pip install -e ".[query]"       # + JMESPath support
uv pip install -e ".[schema]"      # + JSON Schema validation
uv pip install -e ".[web]"         # + Web server dependencies
```

## Usage

### Basic Viewing

```bash
# View JSON file in interactive terminal TUI
jv data.json

# View in browser (opens automatically)
jv data.json -w
jv data.json --web

# Pipe JSON from stdin
cat data.json | jv
curl -s https://api.github.com/users/octocat | jv
echo '{"name": "test"}' | jv
```

### Output Modes (Non-Interactive)

```bash
# Pretty-print JSON to stdout
jv data.json -f
jv data.json --format

# Minify JSON (remove whitespace)
jv data.json -m
jv data.json --minify

# Combine with pipes
curl -s https://api.example.com/data | jv -f > formatted.json
cat ugly.json | jv -m > minified.json
```

### Validation

```bash
# Validate JSON syntax
jv data.json --validate

# Validate against JSON Schema
jv data.json --validate --schema schema.json
jv data.json --validate -s schema.json
```

### JMESPath Queries

Filter and extract data using [JMESPath](https://jmespath.org/) expressions:

```bash
# Extract a specific field
jv data.json -q "name" -f

# Get first item from array
jv data.json -q "users[0]" -f

# Filter array items
jv data.json -q "users[?age > `18`]" -f

# Select specific fields
jv data.json -q "users[*].{name: name, email: email}" -f

# Complex queries
jv data.json -q "items[?status=='active'].price | sum(@)" -f
```

### Comparing Files

```bash
# Compare two JSON files
jv file1.json --diff file2.json

# Output shows:
#   + path: value    (added)
#   - path: value    (removed)
#   ~ path:          (changed)
#     - old_value
#     + new_value
```

### Display Options

```bash
# Expand all nodes on start
jv data.json -e
jv data.json --expand-all

# Expand to specific depth (0-20)
jv data.json -d 2
jv data.json --depth 3

# Use light theme
jv data.json -t light
jv data.json --theme light
```

### Web Server Options

```bash
# Open in browser on custom port
jv data.json -w -p 3000
jv data.json --web --port 9000
```

### Watch Mode

```bash
# Watch file for changes and reload
jv data.json -W
jv data.json --watch
```

## Keyboard Shortcuts (Terminal TUI)

### Navigation

| Key | Action |
|-----|--------|
| `j` / `↓` | Move cursor down |
| `k` / `↑` | Move cursor up |
| `h` / `←` | Collapse node / Go to parent |
| `l` / `→` | Expand node / Enter first child |
| `Enter` | Toggle expand/collapse |
| `g` / `Home` | Go to top |
| `G` / `End` | Go to bottom |

### Expand/Collapse

| Key | Action |
|-----|--------|
| `e` | Expand all nodes |
| `E` | Collapse all nodes |
| `1` - `5` | Expand to depth 1-5 |

### Search

| Key | Action |
|-----|--------|
| `/` or `Ctrl+F` | Open search bar |
| `Enter` | Next search result |
| `n` | Next search result |
| `N` | Previous search result |
| `Escape` | Close search |

### Copy

| Key | Action |
|-----|--------|
| `y` | Copy value to clipboard |
| `Y` | Copy JSONPath to clipboard |

### Other

| Key | Action |
|-----|--------|
| `t` | Toggle dark/light theme |
| `?` | Show help overlay |
| `q` / `Ctrl+C` | Quit |

## CLI Reference

```
Usage: jv [OPTIONS] [FILE]

Arguments:
  [FILE]  JSON file to view. Reads from stdin if not provided.

Options:
  -w, --web                 Open in browser instead of terminal
  -p, --port INTEGER        Port for web server [default: 8888]
  -e, --expand-all          Expand all nodes on start
  -d, --depth INTEGER       Initial expansion depth (0-20)
  -f, --format              Pretty-print JSON and exit
  -m, --minify              Minify JSON and exit
  --validate                Validate JSON and show errors
  -s, --schema PATH         JSON Schema file for validation
  -t, --theme TEXT          Color theme: dark, light [default: dark]
  -q, --query TEXT          JMESPath query to filter JSON
  -W, --watch               Watch file for changes and reload
  --diff PATH               Compare with another JSON file
  -V, --version             Show version and exit
  --help                    Show this message and exit
```

## Examples

### API Response Exploration

```bash
# Explore GitHub API response
curl -s https://api.github.com/repos/python/cpython | jv

# Extract specific data
curl -s https://api.github.com/users/octocat/repos | jv -q "[*].{name: name, stars: stargazers_count}" -f
```

### Configuration File Editing

```bash
# View package.json with expanded dependencies
jv package.json -d 2

# Validate tsconfig against schema
jv tsconfig.json --validate -s https://json.schemastore.org/tsconfig
```

### Data Processing Pipeline

```bash
# Format and save
cat raw.json | jv -f > formatted.json

# Extract and transform
jv data.json -q "users[?active].email" -f | sort | uniq

# Compare before/after
jv original.json --diff modified.json
```

### Large File Handling

```bash
# Start collapsed for large files
jv large-file.json -d 0

# Query specific data from large file
jv large-file.json -q "data[0:10]" -f
```

## Browser Mode Features

When using `jv file.json -w`, the browser viewer includes:

- **Tree View**: Expandable/collapsible JSON tree
- **Search**: Real-time search with highlighting
- **Navigation**: Previous/Next result buttons
- **Expand/Collapse All**: Quick buttons
- **Copy Path**: Click to copy JSONPath
- **Keyboard Shortcuts**: Ctrl+F for search, Escape to clear

## Requirements

- Python 3.10+
- Terminal with color support (for TUI mode)
- Modern web browser (for browser mode)

## Dependencies

**Core:**
- textual >= 1.0.0 (Terminal UI)
- typer >= 0.9.0 (CLI framework)
- rich >= 13.0.0 (Syntax highlighting)
- pyperclip >= 1.8.0 (Clipboard support)

**Optional:**
- jmespath (for `-q` queries)
- jsonschema (for `--validate -s` schema validation)
- uvicorn (for advanced web server features)
- ijson (for streaming large files)
- pyyaml (for YAML export)

## License

MIT
