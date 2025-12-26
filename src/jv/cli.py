"""CLI interface for jv JSON viewer."""

import json
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from jv import __version__
from jv.utils.file_io import format_json, minify_json, read_json_input

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"jv version {__version__}")
        raise typer.Exit()


def main_cli(
    file: Annotated[
        Optional[Path],
        typer.Argument(
            help="JSON file to view. Reads from stdin if not provided.",
        ),
    ] = None,
    web: Annotated[
        bool,
        typer.Option(
            "--web", "-w",
            help="Open in browser instead of terminal.",
        ),
    ] = False,
    port: Annotated[
        int,
        typer.Option(
            "--port", "-p",
            help="Port for web server (with --web).",
        ),
    ] = 8888,
    expand_all: Annotated[
        bool,
        typer.Option(
            "--expand-all", "-e",
            help="Expand all nodes on start.",
        ),
    ] = False,
    depth: Annotated[
        Optional[int],
        typer.Option(
            "--depth", "-d",
            help="Initial expansion depth.",
            min=0,
            max=20,
        ),
    ] = None,
    format_output: Annotated[
        bool,
        typer.Option(
            "--format", "-f",
            help="Pretty-print JSON and exit.",
        ),
    ] = False,
    minify_output: Annotated[
        bool,
        typer.Option(
            "--minify", "-m",
            help="Minify JSON and exit.",
        ),
    ] = False,
    validate: Annotated[
        bool,
        typer.Option(
            "--validate",
            help="Validate JSON and show errors.",
        ),
    ] = False,
    schema: Annotated[
        Optional[Path],
        typer.Option(
            "--schema", "-s",
            help="JSON Schema file for validation.",
        ),
    ] = None,
    theme: Annotated[
        str,
        typer.Option(
            "--theme", "-t",
            help="Color theme: dark, light.",
        ),
    ] = "dark",
    query: Annotated[
        Optional[str],
        typer.Option(
            "--query", "-q",
            help="JMESPath query to filter JSON.",
        ),
    ] = None,
    watch: Annotated[
        bool,
        typer.Option(
            "--watch", "-W",
            help="Watch file for changes and reload.",
        ),
    ] = False,
    diff_file: Annotated[
        Optional[Path],
        typer.Option(
            "--diff",
            help="Compare with another JSON file.",
        ),
    ] = None,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version", "-V",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """
    View and navigate JSON files in terminal or browser.

    Examples:\n
        jv file.json                    View in terminal TUI\n
        jv file.json -w                 Open in browser\n
        cat file.json | jv              Pipe from stdin\n
        jv file.json -f                 Pretty-print to stdout\n
        jv file.json -m                 Minify JSON\n
        jv file.json --validate         Validate JSON\n
        jv file.json -q "users[0]"      JMESPath query\n
        jv file.json --diff other.json  Compare two files
    """
    # Validate file exists if provided
    if file is not None and not file.exists():
        console.print(f"[red]Error:[/] File not found: {file}")
        raise typer.Exit(1)

    # Handle diff mode
    if diff_file is not None:
        if file is None:
            console.print("[red]Error:[/] --diff requires a file argument")
            raise typer.Exit(1)
        if not diff_file.exists():
            console.print(f"[red]Error:[/] Diff file not found: {diff_file}")
            raise typer.Exit(1)
        run_diff(file, diff_file)
        return

    # Read JSON input
    try:
        data, source, raw_content = read_json_input(file)
    except ValueError as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)

    # Get source name for display
    source_name = Path(source).name if source != "stdin" else "stdin"

    # Handle JMESPath query
    if query:
        try:
            import jmespath
            data = jmespath.search(query, data)
            if data is None:
                console.print("[yellow]Query returned no results[/]")
                raise typer.Exit(0)
        except ImportError:
            console.print("[red]Error:[/] jmespath not installed. Run: uv pip install 'jv[query]'")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Query error:[/] {e}")
            raise typer.Exit(1)

    # Handle validation
    if validate:
        console.print("[green]Valid JSON[/]")
        if schema:
            if not schema.exists():
                console.print(f"[red]Error:[/] Schema file not found: {schema}")
                raise typer.Exit(1)
            try:
                import jsonschema
                schema_data = json.loads(schema.read_text())
                jsonschema.validate(data, schema_data)
                console.print("[green]Schema validation passed[/]")
            except ImportError:
                console.print("[red]Error:[/] jsonschema not installed. Run: uv pip install 'jv[schema]'")
                raise typer.Exit(1)
            except jsonschema.ValidationError as e:
                console.print("[red]Schema validation failed:[/]")
                console.print(f"  Path: {'.'.join(str(p) for p in e.path)}")
                console.print(f"  Error: {e.message}")
                raise typer.Exit(1)
        raise typer.Exit(0)

    # Handle output modes (non-interactive)
    if format_output:
        print(format_json(data))
        raise typer.Exit(0)

    if minify_output:
        print(minify_json(data))
        raise typer.Exit(0)

    # Handle watch mode
    if watch and file:
        run_watch_mode(file, data, source_name, web, port, expand_all, depth, theme)
        return

    # Launch viewer
    if web:
        from jv.web.server import run_web_viewer
        run_web_viewer(data, source=source_name, port=port)
    else:
        from jv.tui.app import run_tui
        run_tui(
            data,
            source=source_name,
            expand_all=expand_all,
            expand_depth=depth,
            theme=theme,
        )


def run_diff(file1: Path, file2: Path) -> None:
    """Compare two JSON files and show differences."""
    try:
        data1, _, _ = read_json_input(file1)
        data2, _, _ = read_json_input(file2)
    except ValueError as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)

    differences = compare_json(data1, data2)

    if not differences:
        console.print("[green]Files are identical[/]")
        raise typer.Exit(0)

    console.print(f"[yellow]Found {len(differences)} difference(s):[/]\n")
    for d in differences:
        path, type_, val1, val2 = d
        if type_ == "added":
            console.print(f"[green]+ {path}[/]: {json.dumps(val2)}")
        elif type_ == "removed":
            console.print(f"[red]- {path}[/]: {json.dumps(val1)}")
        elif type_ == "changed":
            console.print(f"[yellow]~ {path}[/]:")
            console.print(f"  [red]- {json.dumps(val1)}[/]")
            console.print(f"  [green]+ {json.dumps(val2)}[/]")


def run_watch_mode(
    file: Path,
    initial_data: dict,
    source_name: str,
    web: bool,
    port: int,
    expand_all: bool,
    depth: Optional[int],
    theme: str,
) -> None:
    """Run viewer with file watching for changes."""
    import time

    console.print(f"[cyan]Watching {file} for changes...[/]")
    console.print("[dim]Press Ctrl+C to stop[/]")

    last_mtime = file.stat().st_mtime

    if web:
        console.print("[yellow]Watch mode with --web is not yet fully implemented.[/]")
        console.print("[yellow]Starting without watch...[/]")
        from jv.web.server import run_web_viewer
        run_web_viewer(initial_data, source=source_name, port=port)
        return

    while True:
        try:
            current_mtime = file.stat().st_mtime
            if current_mtime != last_mtime:
                last_mtime = current_mtime
                console.print(f"[cyan]File changed, reloading...[/]")

                try:
                    data, _, _ = read_json_input(file)
                    from jv.tui.app import run_tui
                    run_tui(
                        data,
                        source=source_name,
                        expand_all=expand_all,
                        expand_depth=depth,
                        theme=theme,
                    )
                except ValueError as e:
                    console.print(f"[red]Error:[/] {e}")

            time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[dim]Watch stopped[/]")
            break


def compare_json(
    obj1: dict | list,
    obj2: dict | list,
    path: str = "$",
) -> list[tuple[str, str, any, any]]:
    """Compare two JSON objects and return differences."""
    differences = []

    if type(obj1) != type(obj2):
        differences.append((path, "changed", obj1, obj2))
        return differences

    if isinstance(obj1, dict):
        all_keys = set(obj1.keys()) | set(obj2.keys())
        for key in sorted(all_keys):
            new_path = f"{path}.{key}"
            if key not in obj1:
                differences.append((new_path, "added", None, obj2[key]))
            elif key not in obj2:
                differences.append((new_path, "removed", obj1[key], None))
            elif obj1[key] != obj2[key]:
                if isinstance(obj1[key], (dict, list)) and isinstance(obj2[key], (dict, list)):
                    differences.extend(compare_json(obj1[key], obj2[key], new_path))
                else:
                    differences.append((new_path, "changed", obj1[key], obj2[key]))

    elif isinstance(obj1, list):
        max_len = max(len(obj1), len(obj2))
        for i in range(max_len):
            new_path = f"{path}[{i}]"
            if i >= len(obj1):
                differences.append((new_path, "added", None, obj2[i]))
            elif i >= len(obj2):
                differences.append((new_path, "removed", obj1[i], None))
            elif obj1[i] != obj2[i]:
                if isinstance(obj1[i], (dict, list)) and isinstance(obj2[i], (dict, list)):
                    differences.extend(compare_json(obj1[i], obj2[i], new_path))
                else:
                    differences.append((new_path, "changed", obj1[i], obj2[i]))

    else:
        if obj1 != obj2:
            differences.append((path, "changed", obj1, obj2))

    return differences


# Create the Typer app
app = typer.Typer(
    name="jv",
    help="A powerful JSON viewer for terminal and browser.",
    add_completion=True,
    no_args_is_help=False,
)

# Register the main function
app.command()(main_cli)


if __name__ == "__main__":
    app()
