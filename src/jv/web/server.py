"""HTTP server for browser-based JSON viewing."""

import json
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any
import socket


def get_html_template(json_data: str, source: str) -> str:
    """Generate HTML page with embedded JSON viewer."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>jv - {source}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #1e1e2e;
            color: #cdd6f4;
            min-height: 100vh;
        }}

        .header {{
            background: #313244;
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #45475a;
        }}

        .header h1 {{
            font-size: 18px;
            font-weight: 600;
            color: #89b4fa;
        }}

        .header .source {{
            color: #a6adc8;
            font-size: 14px;
        }}

        .toolbar {{
            background: #313244;
            padding: 10px 20px;
            display: flex;
            gap: 10px;
            align-items: center;
            border-bottom: 1px solid #45475a;
        }}

        .toolbar input {{
            flex: 1;
            max-width: 400px;
            padding: 8px 12px;
            border: 1px solid #45475a;
            border-radius: 6px;
            background: #1e1e2e;
            color: #cdd6f4;
            font-size: 14px;
        }}

        .toolbar input:focus {{
            outline: none;
            border-color: #89b4fa;
        }}

        .toolbar button {{
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            background: #45475a;
            color: #cdd6f4;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }}

        .toolbar button:hover {{
            background: #585b70;
        }}

        .toolbar button.primary {{
            background: #89b4fa;
            color: #1e1e2e;
        }}

        .toolbar button.primary:hover {{
            background: #b4befe;
        }}

        .search-info {{
            color: #a6adc8;
            font-size: 14px;
            min-width: 80px;
            text-align: right;
        }}

        .container {{
            padding: 20px;
            height: calc(100vh - 110px);
            overflow: auto;
        }}

        .json-tree {{
            font-family: "JetBrains Mono", "Fira Code", Consolas, monospace;
            font-size: 14px;
            line-height: 1.6;
        }}

        .json-item {{
            margin-left: 20px;
        }}

        .json-key {{
            color: #89b4fa;
        }}

        .json-string {{
            color: #a6e3a1;
        }}

        .json-number {{
            color: #fab387;
        }}

        .json-boolean {{
            color: #cba6f7;
        }}

        .json-null {{
            color: #6c7086;
        }}

        .json-bracket {{
            color: #f5c2e7;
        }}

        .collapsible {{
            cursor: pointer;
            user-select: none;
        }}

        .collapsible::before {{
            content: "▼";
            display: inline-block;
            width: 16px;
            color: #6c7086;
            transition: transform 0.2s;
        }}

        .collapsible.collapsed::before {{
            transform: rotate(-90deg);
        }}

        .collapsible.collapsed + .json-children {{
            display: none;
        }}

        .collapsed-preview {{
            color: #6c7086;
            font-style: italic;
        }}

        .highlight {{
            background: #f9e2af;
            color: #1e1e2e;
            padding: 1px 3px;
            border-radius: 3px;
        }}

        .current-highlight {{
            background: #fab387;
            color: #1e1e2e;
        }}

        .path-bar {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: #313244;
            padding: 8px 20px;
            font-family: monospace;
            font-size: 13px;
            color: #a6adc8;
            border-top: 1px solid #45475a;
        }}

        .path-bar .path {{
            color: #89b4fa;
        }}

        ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
        }}

        ::-webkit-scrollbar-track {{
            background: #1e1e2e;
        }}

        ::-webkit-scrollbar-thumb {{
            background: #45475a;
            border-radius: 5px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: #585b70;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>jv - JSON Viewer</h1>
        <span class="source">{source}</span>
    </div>

    <div class="toolbar">
        <input type="text" id="search" placeholder="Search keys and values... (Ctrl+F)">
        <button onclick="prevResult()">← Prev</button>
        <button onclick="nextResult()">Next →</button>
        <span class="search-info" id="search-info"></span>
        <button onclick="expandAll()">Expand All</button>
        <button onclick="collapseAll()">Collapse All</button>
        <button class="primary" onclick="copyPath()">Copy Path</button>
    </div>

    <div class="container">
        <div class="json-tree" id="json-tree"></div>
    </div>

    <div class="path-bar">
        Path: <span class="path" id="current-path">$</span>
    </div>

    <script>
        const jsonData = {json_data};
        let searchResults = [];
        let currentResultIndex = -1;
        let currentPath = "$";

        function escapeHtml(str) {{
            const div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
        }}

        function renderValue(value, key, path) {{
            const type = Array.isArray(value) ? 'array' :
                         value === null ? 'null' :
                         typeof value;

            if (type === 'object' || type === 'array') {{
                const isArray = type === 'array';
                const items = isArray ? value : Object.entries(value);
                const count = isArray ? value.length : Object.keys(value).length;
                const preview = isArray ? `[${{count}} items]` : `{{${{count}} keys}}`;

                let html = `<div class="json-item" data-path="${{escapeHtml(path)}}">`;
                if (key !== null) {{
                    html += `<span class="collapsible" onclick="toggleCollapse(this)">`;
                    html += `<span class="json-key">"${{escapeHtml(String(key))}}"</span>: `;
                }}
                html += `<span class="json-bracket">${{isArray ? '[' : '{{'}}</span>`;
                html += `<span class="collapsed-preview">${{preview}}</span>`;
                if (key !== null) {{
                    html += `</span>`;
                }}

                html += `<div class="json-children">`;
                if (isArray) {{
                    value.forEach((item, i) => {{
                        const itemPath = `${{path}}[${{i}}]`;
                        html += renderValue(item, i, itemPath);
                        if (i < value.length - 1) html += '<span class="json-bracket">,</span>';
                    }});
                }} else {{
                    const entries = Object.entries(value);
                    entries.forEach(([k, v], i) => {{
                        const itemPath = `${{path}}.${{k}}`;
                        html += renderValue(v, k, itemPath);
                        if (i < entries.length - 1) html += '<span class="json-bracket">,</span>';
                    }});
                }}
                html += `</div>`;
                html += `<span class="json-bracket">${{isArray ? ']' : '}}'}}</span>`;
                html += `</div>`;
                return html;
            }}

            let html = `<div class="json-item" data-path="${{escapeHtml(path)}}" onclick="selectPath('${{escapeHtml(path)}}')">`;
            if (key !== null) {{
                html += `<span class="json-key">"${{escapeHtml(String(key))}}"</span>: `;
            }}

            if (type === 'string') {{
                const displayValue = value.length > 100 ? value.substring(0, 100) + '...' : value;
                html += `<span class="json-string">"${{escapeHtml(displayValue)}}"</span>`;
            }} else if (type === 'number') {{
                html += `<span class="json-number">${{value}}</span>`;
            }} else if (type === 'boolean') {{
                html += `<span class="json-boolean">${{value}}</span>`;
            }} else if (type === 'null') {{
                html += `<span class="json-null">null</span>`;
            }}

            html += `</div>`;
            return html;
        }}

        function toggleCollapse(element) {{
            element.classList.toggle('collapsed');
            event.stopPropagation();
        }}

        function expandAll() {{
            document.querySelectorAll('.collapsible').forEach(el => {{
                el.classList.remove('collapsed');
            }});
        }}

        function collapseAll() {{
            document.querySelectorAll('.collapsible').forEach(el => {{
                el.classList.add('collapsed');
            }});
        }}

        function selectPath(path) {{
            currentPath = path;
            document.getElementById('current-path').textContent = path;
        }}

        function copyPath() {{
            navigator.clipboard.writeText(currentPath).then(() => {{
                const btn = event.target;
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                setTimeout(() => btn.textContent = originalText, 1000);
            }});
        }}

        function search(query) {{
            // Remove existing highlights
            document.querySelectorAll('.highlight, .current-highlight').forEach(el => {{
                el.outerHTML = el.textContent;
            }});

            searchResults = [];
            currentResultIndex = -1;

            if (!query) {{
                updateSearchInfo();
                return;
            }}

            const regex = new RegExp(escapeRegex(query), 'gi');
            const elements = document.querySelectorAll('.json-key, .json-string');

            elements.forEach(el => {{
                if (el.textContent.toLowerCase().includes(query.toLowerCase())) {{
                    const html = el.innerHTML.replace(regex, match => {{
                        return `<span class="highlight">${{match}}</span>`;
                    }});
                    el.innerHTML = html;
                    searchResults.push(...el.querySelectorAll('.highlight'));
                }}
            }});

            if (searchResults.length > 0) {{
                currentResultIndex = 0;
                highlightCurrent();
            }}
            updateSearchInfo();
        }}

        function escapeRegex(str) {{
            return str.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
        }}

        function updateSearchInfo() {{
            const info = document.getElementById('search-info');
            if (searchResults.length === 0) {{
                info.textContent = document.getElementById('search').value ? 'No results' : '';
            }} else {{
                info.textContent = `${{currentResultIndex + 1}} / ${{searchResults.length}}`;
            }}
        }}

        function highlightCurrent() {{
            searchResults.forEach((el, i) => {{
                el.classList.remove('current-highlight');
                if (i === currentResultIndex) {{
                    el.classList.add('current-highlight');
                    el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});

                    // Expand parent nodes
                    let parent = el.closest('.json-children');
                    while (parent) {{
                        const collapsible = parent.previousElementSibling;
                        if (collapsible && collapsible.classList.contains('collapsible')) {{
                            collapsible.classList.remove('collapsed');
                        }}
                        parent = parent.parentElement.closest('.json-children');
                    }}
                }}
            }});
        }}

        function nextResult() {{
            if (searchResults.length === 0) return;
            currentResultIndex = (currentResultIndex + 1) % searchResults.length;
            highlightCurrent();
            updateSearchInfo();
        }}

        function prevResult() {{
            if (searchResults.length === 0) return;
            currentResultIndex = (currentResultIndex - 1 + searchResults.length) % searchResults.length;
            highlightCurrent();
            updateSearchInfo();
        }}

        // Initialize
        document.getElementById('json-tree').innerHTML = renderValue(jsonData, null, '$');

        // Search input handler
        let searchTimeout;
        document.getElementById('search').addEventListener('input', (e) => {{
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => search(e.target.value), 200);
        }});

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {{
            if (e.ctrlKey && e.key === 'f') {{
                e.preventDefault();
                document.getElementById('search').focus();
            }}
            if (e.key === 'Enter' && document.activeElement.id === 'search') {{
                nextResult();
            }}
            if (e.key === 'Escape') {{
                document.getElementById('search').value = '';
                search('');
                document.getElementById('search').blur();
            }}
        }});
    </script>
</body>
</html>'''


class JSONRequestHandler(SimpleHTTPRequestHandler):
    """Custom request handler for serving JSON viewer."""

    def __init__(self, *args, html_content: str = "", **kwargs):
        self.html_content = html_content
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(self.html_content.encode()))
            self.end_headers()
            self.wfile.write(self.html_content.encode())
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        """Suppress logging."""
        pass


def find_free_port(start_port: int = 8888) -> int:
    """Find a free port starting from the given port."""
    port = start_port
    while port < start_port + 100:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return port
        except OSError:
            port += 1
    return start_port


def run_web_viewer(
    json_data: Any,
    source: str = "JSON",
    port: int = 8888,
) -> None:
    """
    Run the browser-based JSON viewer.

    Args:
        json_data: The parsed JSON data to display.
        source: Name of the source (filename or 'stdin').
        port: Port to run the server on.
    """
    # Serialize JSON for embedding in HTML
    json_str = json.dumps(json_data, ensure_ascii=False)
    html_content = get_html_template(json_str, source)

    # Find a free port
    actual_port = find_free_port(port)

    # Create handler with HTML content
    def handler(*args, **kwargs):
        return JSONRequestHandler(*args, html_content=html_content, **kwargs)

    server = HTTPServer(("localhost", actual_port), handler)
    url = f"http://localhost:{actual_port}"

    print(f"Starting JSON viewer at {url}")
    print("Press Ctrl+C to stop the server")

    # Open browser in a separate thread
    def open_browser():
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.shutdown()
