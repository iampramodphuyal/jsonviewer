"""Search bar widget for jv."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Input, Label, Static


class SearchBar(Static):
    """A search bar widget with result count display."""

    DEFAULT_CSS = """
    SearchBar {
        height: 3;
        padding: 0 1;
        background: $surface;
        border-bottom: solid $primary;
    }

    SearchBar Horizontal {
        width: 100%;
        height: 100%;
    }

    SearchBar Input {
        width: 1fr;
        margin-right: 1;
    }

    SearchBar .search-info {
        width: auto;
        min-width: 12;
        text-align: right;
        padding: 0 1;
    }
    """

    class SearchSubmitted(Message):
        """Message sent when search is submitted."""

        def __init__(self, query: str) -> None:
            super().__init__()
            self.query = query

    class SearchCleared(Message):
        """Message sent when search is cleared."""

    class SearchNext(Message):
        """Message to go to next result."""

    class SearchPrev(Message):
        """Message to go to previous result."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._result_count = 0
        self._current_idx = 0

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("Search: ", id="search-label")
            yield Input(
                placeholder="Type to search... (Enter to find, Esc to close)",
                id="search-input",
            )
            yield Label("", id="search-info", classes="search-info")

    def on_mount(self) -> None:
        """Focus the input when mounted."""
        self.query_one("#search-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes for live search."""
        if event.value:
            self.post_message(self.SearchSubmitted(event.value))
        else:
            self.post_message(self.SearchCleared())
            self.update_info(0, 0)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key - go to next result."""
        if event.value:
            self.post_message(self.SearchNext())

    def on_key(self, event) -> None:
        """Handle special keys."""
        if event.key == "escape":
            self.post_message(self.SearchCleared())
        elif event.key == "shift+enter":
            self.post_message(self.SearchPrev())

    def update_info(self, current: int, total: int) -> None:
        """Update the search result info display."""
        self._result_count = total
        self._current_idx = current

        info_label = self.query_one("#search-info", Label)
        if total == 0:
            info_label.update("[dim]No results[/]")
        else:
            info_label.update(f"[bold]{current}[/]/[dim]{total}[/]")

    def get_query(self) -> str:
        """Get the current search query."""
        return self.query_one("#search-input", Input).value

    def clear(self) -> None:
        """Clear the search input."""
        self.query_one("#search-input", Input).value = ""
        self.update_info(0, 0)
