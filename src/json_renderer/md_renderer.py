"""
JSON → Markdown renderer.

Produces clean, readable Markdown from any JSON structure.
Handles unicode, dollar signs, embedded markdown (passed as-is),
and deeply nested structures without breaking.
"""

from __future__ import annotations

import json
from typing import Any

from json_renderer.utils import escape_md_text, is_markdown_content

# ─── Rendering logic ─────────────────────────────────────────────────────────


def _render_value(value: Any, indent: int = 0, *, in_list: bool = False) -> str:
    """Render a single JSON value to a Markdown fragment."""
    if value is None:
        return "`null`"

    if isinstance(value, bool):
        return f"`{'true' if value else 'false'}`"

    if isinstance(value, (int, float)):
        return f"`{value}`"

    if isinstance(value, str):
        if is_markdown_content(value):
            # Pass markdown content as-is — no double-processing
            return value
        return escape_md_text(value)

    if isinstance(value, dict):
        return _render_object(value, indent)

    if isinstance(value, list):
        return _render_array(value, indent)

    # Fallback
    return escape_md_text(str(value))


def _render_key(key: str) -> str:
    """Render a JSON key as bold Markdown with special chars escaped."""
    escaped = escape_md_text(str(key))
    return f"**{escaped}**"


def _render_object(obj: dict[str, Any], indent: int = 0) -> str:
    """Render a JSON object as a Markdown section."""
    if not obj:
        return "*empty object*"

    lines: list[str] = []
    prefix = "  " * indent

    for key, value in obj.items():
        rendered_key = _render_key(key)

        if isinstance(value, dict):
            lines.append(f"{prefix}- {rendered_key}:")
            nested = _render_object(value, indent + 1)
            lines.append(nested)

        elif isinstance(value, list):
            lines.append(f"{prefix}- {rendered_key}: *(array of {len(value)} items)*")
            nested = _render_array(value, indent + 1)
            lines.append(nested)

        elif isinstance(value, str) and is_markdown_content(value):
            lines.append(f"{prefix}- {rendered_key}:")
            lines.append("")
            # Indent the markdown content block
            for md_line in value.split("\n"):
                lines.append(f"{prefix}  {md_line}")
            lines.append("")

        else:
            rendered_val = _render_value(value, indent)
            lines.append(f"{prefix}- {rendered_key}: {rendered_val}")

    return "\n".join(lines)


def _render_array(arr: list[Any], indent: int = 0) -> str:
    """Render a JSON array as a Markdown list."""
    if not arr:
        return f"{'  ' * indent}*empty array*"

    lines: list[str] = []
    prefix = "  " * indent

    for idx, item in enumerate(arr):
        if isinstance(item, dict):
            lines.append(f"{prefix}- **[{idx}]**:")
            nested = _render_object(item, indent + 1)
            lines.append(nested)
        elif isinstance(item, list):
            lines.append(f"{prefix}- **[{idx}]**: *(array of {len(item)} items)*")
            nested = _render_array(item, indent + 1)
            lines.append(nested)
        else:
            rendered = _render_value(item, indent)
            lines.append(f"{prefix}- {rendered}")

    return "\n".join(lines)


# ─── Public API ───────────────────────────────────────────────────────────────


def render_json_to_markdown(
    data: dict | list | str,
    title: str | None = "JSON Document",
) -> str:
    """
    Render a JSON value to a **Markdown document**.

    Parameters
    ----------
    data : dict, list, or str
        Parsed JSON (``dict``/``list``) or a raw JSON string.
    title : str or None
        Optional document title rendered as an ``# H1``.
        Pass ``None`` to omit.

    Returns
    -------
    str
        A Markdown-formatted string.
    """
    if isinstance(data, str):
        data = json.loads(data)

    sections: list[str] = []

    if title:
        sections.append(f"# {title}")
        sections.append("")

    body = _render_value(data)
    sections.append(body)
    sections.append("")  # trailing newline

    return "\n".join(sections)
