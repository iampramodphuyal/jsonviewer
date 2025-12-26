"""Main Textual application for jv JSON viewer."""

from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Label, Static

from jv.core.path import get_jsonpath
from jv.core.search import search_json, SearchResult
from jv.tui.widgets.json_tree import JSONTree
from jv.tui.widgets.search_bar import SearchBar


class HelpScreen(ModalScreen[None]):
    """Modal screen showing keyboard shortcuts."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("?", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        yield Container(
            Static("[bold]jv - JSON Viewer Help[/]", classes="help-title"),
            Static(""),
            Static("[bold cyan]Navigation[/]", classes="help-section"),
            Horizontal(
                Static("j / ↓", classes="help-key"),
                Static("Move down", classes="help-desc"),
            ),
            Horizontal(
                Static("k / ↑", classes="help-key"),
                Static("Move up", classes="help-desc"),
            ),
            Horizontal(
                Static("h / ←", classes="help-key"),
                Static("Collapse / Go to parent", classes="help-desc"),
            ),
            Horizontal(
                Static("l / →", classes="help-key"),
                Static("Expand / Enter node", classes="help-desc"),
            ),
            Horizontal(
                Static("Enter", classes="help-key"),
                Static("Toggle expand/collapse", classes="help-desc"),
            ),
            Horizontal(
                Static("g / Home", classes="help-key"),
                Static("Go to top", classes="help-desc"),
            ),
            Horizontal(
                Static("G / End", classes="help-key"),
                Static("Go to bottom", classes="help-desc"),
            ),
            Static(""),
            Static("[bold cyan]Expand/Collapse[/]", classes="help-section"),
            Horizontal(
                Static("e", classes="help-key"),
                Static("Expand all nodes", classes="help-desc"),
            ),
            Horizontal(
                Static("E", classes="help-key"),
                Static("Collapse all nodes", classes="help-desc"),
            ),
            Horizontal(
                Static("1-5", classes="help-key"),
                Static("Expand to depth N", classes="help-desc"),
            ),
            Static(""),
            Static("[bold cyan]Search[/]", classes="help-section"),
            Horizontal(
                Static("/ or Ctrl+F", classes="help-key"),
                Static("Open search", classes="help-desc"),
            ),
            Horizontal(
                Static("n", classes="help-key"),
                Static("Next search result", classes="help-desc"),
            ),
            Horizontal(
                Static("N", classes="help-key"),
                Static("Previous search result", classes="help-desc"),
            ),
            Horizontal(
                Static("Escape", classes="help-key"),
                Static("Close search", classes="help-desc"),
            ),
            Static(""),
            Static("[bold cyan]Copy[/]", classes="help-section"),
            Horizontal(
                Static("y", classes="help-key"),
                Static("Copy value", classes="help-desc"),
            ),
            Horizontal(
                Static("Y", classes="help-key"),
                Static("Copy JSONPath", classes="help-desc"),
            ),
            Static(""),
            Static("[bold cyan]Other[/]", classes="help-section"),
            Horizontal(
                Static("t", classes="help-key"),
                Static("Toggle theme", classes="help-desc"),
            ),
            Horizontal(
                Static("?", classes="help-key"),
                Static("Show this help", classes="help-desc"),
            ),
            Horizontal(
                Static("q", classes="help-key"),
                Static("Quit", classes="help-desc"),
            ),
            Static(""),
            Static("[dim]Press Escape or ? to close[/]", classes="help-title"),
            id="help-overlay",
        )


class JSONViewerApp(App[None]):
    """Main JSON viewer application."""

    CSS_PATH = Path(__file__).parent / "styles" / "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("?", "help", "Help", show=True),
        Binding("/", "search", "Search", show=True),
        Binding("ctrl+f", "search", "Search", show=False),
        Binding("escape", "close_search", "Close Search", show=False),
        Binding("n", "next_result", "Next", show=False),
        Binding("N", "prev_result", "Previous", show=False),
        Binding("t", "toggle_theme", "Theme", show=True),
        Binding("g", "go_top", "Top", show=False),
        Binding("G", "go_bottom", "Bottom", show=False),
        Binding("j", "cursor_down", show=False),
        Binding("k", "cursor_up", show=False),
        Binding("h", "cursor_left", show=False),
        Binding("l", "cursor_right", show=False),
    ]

    def __init__(
        self,
        json_data: Any,
        source: str = "JSON",
        expand_depth: int | None = 1,
        theme: str = "dark",
        **kwargs: Any,
    ) -> None:
        """
        Initialize the JSON viewer app.

        Args:
            json_data: The parsed JSON data to display.
            source: Name of the source file or 'stdin'.
            expand_depth: Initial expansion depth.
            theme: Color theme ('dark' or 'light').
        """
        super().__init__(**kwargs)
        self.json_data = json_data
        self.source = source
        self.expand_depth = expand_depth
        self.initial_theme = theme
        self._search_visible = False
        self._search_results: list[SearchResult] = []
        self._current_result_idx = 0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="main-container"):
            yield JSONTree(
                self.json_data,
                source=self.source,
                expand_depth=self.expand_depth,
                id="json-tree",
            )
        yield Footer()

    def on_mount(self) -> None:
        """Configure app on mount."""
        self.title = f"jv - {self.source}"
        self.sub_title = "JSON Viewer"
        if self.initial_theme == "light":
            self.theme = "textual-light"
        else:
            self.theme = "textual-dark"

    def action_help(self) -> None:
        """Show help screen."""
        self.push_screen(HelpScreen())

    def action_search(self) -> None:
        """Open search bar."""
        if self._search_visible:
            return

        self._search_visible = True
        search_bar = SearchBar(id="search-bar")
        self.query_one("#main-container").mount(search_bar, before=0)
        search_bar.focus()

    def action_close_search(self) -> None:
        """Close search bar."""
        if not self._search_visible:
            return

        self._search_visible = False
        try:
            search_bar = self.query_one("#search-bar")
            search_bar.remove()
        except Exception:
            pass

        self._search_results = []
        self._current_result_idx = 0
        tree = self.query_one("#json-tree", JSONTree)
        tree.set_search_results([])
        tree.focus()

    def on_search_bar_search_submitted(self, event: SearchBar.SearchSubmitted) -> None:
        """Handle search query."""
        self._search_results = list(
            search_json(self.json_data, event.query, case_sensitive=False)
        )
        self._current_result_idx = 0

        tree = self.query_one("#json-tree", JSONTree)
        tree.set_search_results(self._search_results)

        search_bar = self.query_one("#search-bar", SearchBar)
        if self._search_results:
            search_bar.update_info(1, len(self._search_results))
            self._navigate_to_current_result()
        else:
            search_bar.update_info(0, 0)

    def on_search_bar_search_cleared(self, event: SearchBar.SearchCleared) -> None:
        """Handle search clear."""
        self.action_close_search()

    def on_search_bar_search_next(self, event: SearchBar.SearchNext) -> None:
        """Go to next search result."""
        self.action_next_result()

    def on_search_bar_search_prev(self, event: SearchBar.SearchPrev) -> None:
        """Go to previous search result."""
        self.action_prev_result()

    def action_next_result(self) -> None:
        """Navigate to next search result."""
        if not self._search_results:
            return

        self._current_result_idx = (self._current_result_idx + 1) % len(self._search_results)
        self._navigate_to_current_result()

        if self._search_visible:
            search_bar = self.query_one("#search-bar", SearchBar)
            search_bar.update_info(self._current_result_idx + 1, len(self._search_results))

    def action_prev_result(self) -> None:
        """Navigate to previous search result."""
        if not self._search_results:
            return

        self._current_result_idx = (self._current_result_idx - 1) % len(self._search_results)
        self._navigate_to_current_result()

        if self._search_visible:
            search_bar = self.query_one("#search-bar", SearchBar)
            search_bar.update_info(self._current_result_idx + 1, len(self._search_results))

    def _navigate_to_current_result(self) -> None:
        """Navigate tree to current search result."""
        if not self._search_results:
            return

        result = self._search_results[self._current_result_idx]
        tree = self.query_one("#json-tree", JSONTree)
        tree.navigate_to_path(result.path)

    def action_toggle_theme(self) -> None:
        """Toggle between light and dark theme."""
        if self.theme == "textual-dark":
            self.theme = "textual-light"
        else:
            self.theme = "textual-dark"

    def action_go_top(self) -> None:
        """Go to top of tree."""
        tree = self.query_one("#json-tree", JSONTree)
        tree.select_node(tree.root)
        tree.scroll_home()

    def action_go_bottom(self) -> None:
        """Go to bottom of tree."""
        tree = self.query_one("#json-tree", JSONTree)
        # Find last visible node
        tree.scroll_end()

    def action_cursor_down(self) -> None:
        """Move cursor down (vim-style j)."""
        tree = self.query_one("#json-tree", JSONTree)
        tree.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up (vim-style k)."""
        tree = self.query_one("#json-tree", JSONTree)
        tree.action_cursor_up()

    def action_cursor_left(self) -> None:
        """Collapse or go to parent (vim-style h)."""
        tree = self.query_one("#json-tree", JSONTree)
        node = tree.cursor_node
        if node and node.is_expanded:
            node.collapse()
        elif node and node.parent:
            tree.select_node(node.parent)

    def action_cursor_right(self) -> None:
        """Expand or enter node (vim-style l)."""
        tree = self.query_one("#json-tree", JSONTree)
        node = tree.cursor_node
        if node and node.allow_expand and not node.is_expanded:
            node.expand()
        elif node and node.children:
            tree.select_node(node.children[0])

    def on_tree_node_selected(self, event) -> None:
        """Update status when node is selected."""
        tree = self.query_one("#json-tree", JSONTree)
        path = tree.get_current_path()
        self.sub_title = path


def run_tui(
    json_data: Any,
    source: str = "JSON",
    expand_all: bool = False,
    expand_depth: int | None = None,
    theme: str = "dark",
) -> None:
    """
    Run the TUI JSON viewer.

    Args:
        json_data: The parsed JSON data to display.
        source: Name of the source (filename or 'stdin').
        expand_all: Whether to expand all nodes initially.
        expand_depth: Initial expansion depth (overrides expand_all).
        theme: Color theme ('dark' or 'light').
    """
    if expand_all:
        depth = None  # None means expand all
    elif expand_depth is not None:
        depth = expand_depth
    else:
        depth = 1  # Default: expand first level

    app = JSONViewerApp(
        json_data=json_data,
        source=source,
        expand_depth=depth,
        theme=theme,
    )
    app.run()
