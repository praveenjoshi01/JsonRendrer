"""
Shared utilities for escaping and sanitisation across both renderers.
"""

from __future__ import annotations

import html
import re

import bleach

# ─── Markdown detection heuristic ─────────────────────────────────────────────

_MD_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^#{1,6}\s", re.MULTILINE),        # headings
    re.compile(r"\*\*.+?\*\*"),                      # bold
    re.compile(r"\*.+?\*"),                          # italic
    re.compile(r"`.+?`"),                            # inline code
    re.compile(r"```"),                              # code fences
    re.compile(r"^\s*[-*+]\s", re.MULTILINE),       # unordered lists
    re.compile(r"^\s*\d+\.\s", re.MULTILINE),       # ordered lists
    re.compile(r"\[.+?\]\(.+?\)"),                   # links
    re.compile(r"!\[.*?\]\(.+?\)"),                  # images
]


def is_markdown_content(text: str) -> bool:
    """Return True if *text* looks like it contains Markdown formatting."""
    matches = sum(1 for p in _MD_PATTERNS if p.search(text))
    return matches >= 2  # require at least 2 different MD features


# ─── HTML escaping ────────────────────────────────────────────────────────────

def escape_html_text(text: str) -> str:
    """
    HTML-entity-escape a string, *including* dollar signs.

    This prevents:
    - XSS via ``<script>``
    - Accidental MathJax/LaTeX interpretation via ``$``
    """
    escaped = html.escape(text, quote=True)
    escaped = escaped.replace("$", "&#36;")
    return escaped


# ─── Markdown escaping ───────────────────────────────────────────────────────

_MD_SPECIAL_CHARS = r"\`*_{}[]()#+-.!|~>$"


def escape_md_text(text: str) -> str:
    """
    Backslash-escape characters that have special meaning in Markdown.

    Used for *keys* and plain-text values — NOT for values that are
    already valid Markdown (those are passed through as-is).
    """
    out: list[str] = []
    for ch in text:
        if ch in _MD_SPECIAL_CHARS:
            out.append(f"\\{ch}")
        else:
            out.append(ch)
    return "".join(out)


# ─── HTML sanitisation (for embedded markdown rendered to HTML) ──────────────

_ALLOWED_TAGS = [
    "p", "br", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "strong", "em", "code", "pre",
    "blockquote",
    "a", "img",
    "table", "thead", "tbody", "tr", "th", "td",
    "hr", "del", "ins", "sub", "sup",
    "span", "div",
]

_ALLOWED_ATTRS = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
    "td": ["align"],
    "th": ["align"],
}


def sanitise_html(raw_html: str) -> str:
    """
    Sanitise HTML produced by the Markdown renderer so it is safe to
    embed inside our output document.  Strips ``<script>``, event
    handlers, etc.
    """
    return bleach.clean(
        raw_html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        strip=True,
    )
