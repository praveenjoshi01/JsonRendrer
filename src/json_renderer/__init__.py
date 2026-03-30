"""
JsonRenderer — Safely render arbitrary JSON to HTML and Markdown.

Handles unicode, dollar signs, embedded markdown, XSS payloads,
and every edge case that typically breaks renderers.
"""

__version__ = "1.0.0"

from json_renderer.html_renderer import render_json_to_html
from json_renderer.md_renderer import render_json_to_markdown

__all__ = ["render_json_to_html", "render_json_to_markdown"]
