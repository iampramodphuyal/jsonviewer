"""Cross-platform clipboard utilities."""

import subprocess
import sys


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to system clipboard.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        # Fallback for systems without pyperclip working
        return _fallback_copy(text)


def _fallback_copy(text: str) -> bool:
    """Fallback clipboard copy using system commands."""
    try:
        if sys.platform == "darwin":
            # macOS
            subprocess.run(
                ["pbcopy"],
                input=text.encode("utf-8"),
                check=True,
            )
        elif sys.platform == "linux":
            # Try wl-copy (Wayland) first, then xclip (X11)
            try:
                subprocess.run(
                    ["wl-copy"],
                    input=text.encode("utf-8"),
                    check=True,
                )
            except FileNotFoundError:
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=text.encode("utf-8"),
                    check=True,
                )
        elif sys.platform == "win32":
            subprocess.run(
                ["clip"],
                input=text.encode("utf-16le"),
                check=True,
            )
        else:
            return False
        return True
    except Exception:
        return False
