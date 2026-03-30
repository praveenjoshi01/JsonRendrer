"""
JSON → HTML renderer.

Produces a self-contained, styled HTML document from any JSON structure.
Handles unicode, dollar signs, embedded markdown, XSS payloads, and deeply
nested structures without breaking.
"""

from __future__ import annotations

import json
from typing import Any

import markdown as md_lib

from json_renderer.utils import (
    escape_html_text,
    is_markdown_content,
    sanitise_html,
)

# ─── CSS theme ────────────────────────────────────────────────────────────────

_CSS = """
:root {
    --bg-primary: #0f1117;
    --bg-secondary: #1a1d2e;
    --bg-tertiary: #252840;
    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --accent: #818cf8;
    --accent-dim: #6366f180;
    --key-color: #c084fc;
    --string-color: #34d399;
    --number-color: #fbbf24;
    --bool-color: #f472b6;
    --null-color: #64748b;
    --border: #334155;
    --shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
    --radius: 8px;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    padding: 2rem;
    line-height: 1.6;
}

h1 {
    font-size: 1.8rem;
    background: linear-gradient(135deg, var(--accent), #a78bfa, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 1.5rem;
    font-weight: 700;
    letter-spacing: -0.02em;
}

.json-container {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    overflow: hidden;
}

/* ── Object table ───────────────────────────────────────── */

table.json-object {
    width: 100%;
    border-collapse: collapse;
}

table.json-object tr {
    transition: background 0.15s;
}

table.json-object tr:hover {
    background: var(--bg-tertiary);
}

table.json-object td {
    padding: 0.65rem 1rem;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
}

td.json-key {
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 0.9rem;
    color: var(--key-color);
    white-space: nowrap;
    width: 1%;
    font-weight: 600;
    position: relative;
    padding-left: 1.4rem;
}

td.json-key::before {
    content: '▸';
    position: absolute;
    left: 0.4rem;
    color: var(--accent-dim);
    font-size: 0.7rem;
    top: 0.8rem;
}

td.json-value {
    font-size: 0.9rem;
}

/* ── Array list ─────────────────────────────────────────── */

ul.json-array {
    list-style: none;
    padding-left: 0;
}

ul.json-array > li {
    padding: 0.5rem 1rem;
    border-bottom: 1px solid var(--border);
    position: relative;
    padding-left: 2rem;
}

ul.json-array > li::before {
    content: attr(data-index);
    position: absolute;
    left: 0.6rem;
    color: var(--text-secondary);
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    opacity: 0.6;
}

ul.json-array > li:last-child {
    border-bottom: none;
}

/* ── Value types ────────────────────────────────────────── */

.json-string { color: var(--string-color); }
.json-number { color: var(--number-color); font-family: 'JetBrains Mono', monospace; }
.json-bool   { color: var(--bool-color); font-style: italic; }
.json-null   { color: var(--null-color); font-style: italic; }

.json-string::before, .json-string::after { content: '"'; opacity: 0.4; }

/* ── Embedded markdown ──────────────────────────────────── */

.md-rendered {
    background: var(--bg-tertiary);
    border-left: 3px solid var(--accent);
    border-radius: 4px;
    padding: 0.6rem 0.9rem;
    margin: 0.3rem 0;
    font-size: 0.88rem;
    line-height: 1.7;
}

.md-rendered h1, .md-rendered h2, .md-rendered h3,
.md-rendered h4, .md-rendered h5, .md-rendered h6 {
    color: var(--accent);
    margin: 0.6rem 0 0.3rem;
}

.md-rendered code {
    background: var(--bg-primary);
    padding: 0.15rem 0.4rem;
    border-radius: 3px;
    font-size: 0.85em;
}

.md-rendered pre {
    background: var(--bg-primary);
    padding: 0.8rem;
    border-radius: 4px;
    overflow-x: auto;
    margin: 0.5rem 0;
}

.md-rendered ul, .md-rendered ol {
    padding-left: 1.5rem;
    margin: 0.3rem 0;
}

.md-rendered a {
    color: var(--accent);
    text-decoration: underline;
}

/* ── Nested container labels ────────────────────────────── */

.json-type-badge {
    display: inline-block;
    font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    padding: 0.1rem 0.45rem;
    border-radius: 3px;
    margin-bottom: 0.3rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
}

.badge-object {
    background: #6366f120;
    color: var(--accent);
    border: 1px solid var(--accent-dim);
}

.badge-array {
    background: #f59e0b15;
    color: var(--number-color);
    border: 1px solid #f59e0b40;
}

/* ── Empty indicator ────────────────────────────────────── */

.json-empty {
    color: var(--null-color);
    font-style: italic;
    opacity: 0.7;
}
"""

# ─── Rendering logic ─────────────────────────────────────────────────────────


def _render_value(value: Any) -> str:
    """Render a single JSON value to an HTML fragment."""
    if value is None:
        return '<span class="json-null">null</span>'

    if isinstance(value, bool):
        return f'<span class="json-bool">{"true" if value else "false"}</span>'

    if isinstance(value, (int, float)):
        return f'<span class="json-number">{value}</span>'

    if isinstance(value, str):
        if is_markdown_content(value):
            raw_html = md_lib.markdown(
                value,
                extensions=["fenced_code", "tables", "nl2br"],
            )
            safe_html = sanitise_html(raw_html)
            return f'<div class="md-rendered">{safe_html}</div>'
        return f'<span class="json-string">{escape_html_text(value)}</span>'

    if isinstance(value, dict):
        return _render_object(value)

    if isinstance(value, list):
        return _render_array(value)

    # Fallback — stringify anything unexpected
    return f'<span class="json-string">{escape_html_text(str(value))}</span>'


def _render_object(obj: dict[str, Any]) -> str:
    """Render a JSON object as an HTML table."""
    if not obj:
        return '<span class="json-empty">{ }</span>'

    rows: list[str] = []
    for key, value in obj.items():
        escaped_key = escape_html_text(str(key))
        rendered_value = _render_value(value)

        # Add type badge for nested structures
        badge = ""
        if isinstance(value, dict):
            badge = '<span class="json-type-badge badge-object">object</span><br>'
        elif isinstance(value, list):
            badge = f'<span class="json-type-badge badge-array">array[{len(value)}]</span><br>'

        rows.append(
            f"<tr>"
            f'<td class="json-key">{escaped_key}</td>'
            f'<td class="json-value">{badge}{rendered_value}</td>'
            f"</tr>"
        )

    return (
        '<div class="json-container">'
        '<table class="json-object">'
        f"{''.join(rows)}"
        "</table>"
        "</div>"
    )


def _render_array(arr: list[Any]) -> str:
    """Render a JSON array as an HTML unordered list."""
    if not arr:
        return '<span class="json-empty">[ ]</span>'

    items: list[str] = []
    for idx, item in enumerate(arr):
        rendered = _render_value(item)
        items.append(f'<li data-index="{idx}">{rendered}</li>')

    return f'<ul class="json-array">{"".join(items)}</ul>'


# ─── Public API ───────────────────────────────────────────────────────────────


def render_json_to_html(
    data: dict | list | str,
    title: str = "JSON Renderer",
) -> str:
    """
    Render a JSON value to a **self-contained HTML document**.

    Parameters
    ----------
    data : dict, list, or str
        Parsed JSON (``dict``/``list``) or a raw JSON string.
    title : str
        HTML ``<title>`` and visible heading.

    Returns
    -------
    str
        A complete HTML document string.
    """
    if isinstance(data, str):
        data = json.loads(data)

    body = _render_value(data)
    escaped_title = escape_html_text(title)

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"  <title>{escaped_title}</title>\n"
        '  <link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">\n'
        f"  <style>{_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        f"  <h1>{escaped_title}</h1>\n"
        f"  {body}\n"
        "</body>\n"
        "</html>"
    )
