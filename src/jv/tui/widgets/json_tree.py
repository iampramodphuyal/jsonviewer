"""JSON Tree widget for displaying JSON data with fold/unfold."""

from typing import Any

from rich.highlighter import ReprHighlighter
from rich.text import Text
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from jv.core.path import get_jsonpath
from jv.core.search import SearchResult


class JSONTree(Tree[dict[str, Any]]):
    """A tree widget for displaying JSON data with syntax highlighting."""

    BINDINGS = [
        ("e", "expand_all", "Expand All"),
        ("E", "collapse_all", "Collapse All"),
        ("y", "copy_value", "Copy Value"),
        ("Y", "copy_path", "Copy Path"),
        ("1", "expand_depth(1)", "Depth 1"),
        ("2", "expand_depth(2)", "Depth 2"),
        ("3", "expand_depth(3)", "Depth 3"),
        ("4", "expand_depth(4)", "Depth 4"),
        ("5", "expand_depth(5)", "Depth 5"),
    ]

    # Type icons
    ICONS = {
        "dict": "[bold cyan]{}[/]",
        "list": "[bold magenta][][/]",
        "str": "[green]\"[/]",
        "int": "[yellow]#[/]",
        "float": "[yellow]#[/]",
        "bool": "[blue]?[/]",
        "null": "[dim]-[/]",
    }

    def __init__(
        self,
        json_data: Any,
        source: str = "root",
        *,
        expand_depth: int | None = 1,
        **kwargs: Any,
    ) -> None:
        """
        Initialize JSON tree.

        Args:
            json_data: The parsed JSON data to display.
            source: Name of the source (filename or 'stdin').
            expand_depth: Initial expansion depth (None for all, 0 for collapsed).
        """
        super().__init__(source, data={"path": [], "value": json_data}, **kwargs)
        self.json_data = json_data
        self.source = source
        self._expand_depth = expand_depth
        self.highlighter = ReprHighlighter()
        self._search_results: list[SearchResult] = []
        self._current_search_idx: int = -1

    def on_mount(self) -> None:
        """Called when widget is mounted - populate the tree."""
        self._populate_node(self.root, self.json_data, [])
        if self._expand_depth is not None:
            self._expand_to_depth(self.root, self._expand_depth, 0)
        else:
            self.root.expand_all()

    def _get_type_icon(self, value: Any) -> str:
        """Get the icon for a value type."""
        if isinstance(value, dict):
            return self.ICONS["dict"]
        elif isinstance(value, list):
            return self.ICONS["list"]
        elif isinstance(value, str):
            return self.ICONS["str"]
        elif isinstance(value, bool):
            return self.ICONS["bool"]
        elif isinstance(value, int):
            return self.ICONS["int"]
        elif isinstance(value, float):
            return self.ICONS["float"]
        elif value is None:
            return self.ICONS["null"]
        return ""

    def _format_key(self, key: str | int) -> Text:
        """Format a key for display."""
        if isinstance(key, int):
            return Text.from_markup(f"[dim]{key}[/]")
        return Text.from_markup(f"[bold]{key}[/]")

    def _format_value(self, value: Any) -> Text:
        """Format a primitive value for display."""
        if isinstance(value, str):
            # Truncate long strings
            display = value if len(value) <= 100 else value[:97] + "..."
            display = display.replace("\n", "\\n").replace("\t", "\\t")
            return Text.from_markup(f'[green]"{display}"[/]')
        elif isinstance(value, bool):
            return Text.from_markup(f"[blue]{str(value).lower()}[/]")
        elif isinstance(value, (int, float)):
            return Text.from_markup(f"[yellow]{value}[/]")
        elif value is None:
            return Text.from_markup("[dim]null[/]")
        return Text(str(value))

    def _populate_node(
        self,
        node: TreeNode[dict[str, Any]],
        data: Any,
        path: list[str | int],
    ) -> None:
        """Recursively populate the tree from JSON data."""
        if isinstance(data, dict):
            # Set label for dict node
            icon = self._get_type_icon(data)
            count = len(data)
            if path:  # Not root
                key = path[-1]
                label = Text.from_markup(f"{icon} ")
                label.append_text(self._format_key(key))
                label.append_text(Text.from_markup(f" [dim]({count} keys)[/]"))
            else:
                label = Text.from_markup(f"{icon} [bold]{self.source}[/] [dim]({count} keys)[/]")
            node.set_label(label)

            # Add children
            for key, value in data.items():
                child_path = path + [key]
                child = node.add(
                    "",
                    data={"path": child_path, "value": value},
                )
                self._populate_node(child, value, child_path)

        elif isinstance(data, list):
            # Set label for list node
            icon = self._get_type_icon(data)
            count = len(data)
            if path:
                key = path[-1]
                label = Text.from_markup(f"{icon} ")
                label.append_text(self._format_key(key))
                label.append_text(Text.from_markup(f" [dim]({count} items)[/]"))
            else:
                label = Text.from_markup(f"{icon} [bold]{self.source}[/] [dim]({count} items)[/]")
            node.set_label(label)

            # Add children
            for idx, item in enumerate(data):
                child_path = path + [idx]
                child = node.add(
                    "",
                    data={"path": child_path, "value": item},
                )
                self._populate_node(child, item, child_path)

        else:
            # Leaf node (primitive value)
            node.allow_expand = False
            key = path[-1] if path else "value"
            icon = self._get_type_icon(data)

            label = Text.from_markup(f"{icon} ")
            label.append_text(self._format_key(key))
            label.append_text(Text(": "))
            label.append_text(self._format_value(data))
            node.set_label(label)

    def _expand_to_depth(
        self,
        node: TreeNode[dict[str, Any]],
        max_depth: int,
        current_depth: int,
    ) -> None:
        """Expand tree to a specific depth."""
        if current_depth < max_depth:
            node.expand()
            for child in node.children:
                self._expand_to_depth(child, max_depth, current_depth + 1)
        else:
            node.collapse()

    def action_expand_all(self) -> None:
        """Expand all nodes."""
        self.root.expand_all()

    def action_collapse_all(self) -> None:
        """Collapse all nodes."""
        self.root.collapse_all()
        self.root.expand()  # Keep root expanded

    def action_expand_depth(self, depth: int) -> None:
        """Expand to specific depth."""
        self.root.collapse_all()
        self._expand_to_depth(self.root, depth, 0)

    def action_copy_value(self) -> None:
        """Copy the current node's value to clipboard."""
        import json
        from jv.utils.clipboard import copy_to_clipboard

        node = self.cursor_node
        if node and node.data:
            value = node.data.get("value")
            if isinstance(value, (dict, list)):
                text = json.dumps(value, indent=2, ensure_ascii=False)
            else:
                text = str(value) if value is not None else "null"
            if copy_to_clipboard(text):
                self.notify("Value copied to clipboard")
            else:
                self.notify("Failed to copy to clipboard", severity="error")

    def action_copy_path(self) -> None:
        """Copy the JSONPath of current node to clipboard."""
        from jv.utils.clipboard import copy_to_clipboard

        node = self.cursor_node
        if node and node.data:
            path = node.data.get("path", [])
            jsonpath = get_jsonpath(path)
            if copy_to_clipboard(jsonpath):
                self.notify(f"Copied: {jsonpath}")
            else:
                self.notify("Failed to copy to clipboard", severity="error")

    def get_current_path(self) -> str:
        """Get JSONPath of currently selected node."""
        node = self.cursor_node
        if node and node.data:
            path = node.data.get("path", [])
            return get_jsonpath(path)
        return "$"

    def get_current_value(self) -> Any:
        """Get value of currently selected node."""
        node = self.cursor_node
        if node and node.data:
            return node.data.get("value")
        return None

    def set_search_results(self, results: list[SearchResult]) -> None:
        """Set search results for highlighting."""
        self._search_results = results
        self._current_search_idx = 0 if results else -1

    def next_search_result(self) -> SearchResult | None:
        """Navigate to next search result."""
        if not self._search_results:
            return None
        self._current_search_idx = (self._current_search_idx + 1) % len(self._search_results)
        return self._search_results[self._current_search_idx]

    def prev_search_result(self) -> SearchResult | None:
        """Navigate to previous search result."""
        if not self._search_results:
            return None
        self._current_search_idx = (self._current_search_idx - 1) % len(self._search_results)
        return self._search_results[self._current_search_idx]

    def navigate_to_path(self, path: list[str | int]) -> None:
        """Navigate to a specific path in the tree."""
        node = self.root
        for key in path:
            # Expand current node
            node.expand()
            # Find child with matching key
            for child in node.children:
                if child.data:
                    child_path = child.data.get("path", [])
                    if child_path and child_path[-1] == key:
                        node = child
                        break

        # Select the found node
        self.select_node(node)
        self.scroll_to_node(node)
