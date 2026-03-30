"""
Tests for the JSON → Markdown renderer.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from json_renderer.md_renderer import render_json_to_markdown

FIXTURES_DIR = Path(__file__).parent / "fixtures"
COMPLEX_JSON = FIXTURES_DIR / "complex.json"


@pytest.fixture
def complex_data() -> dict:
    return json.loads(COMPLEX_JSON.read_text(encoding="utf-8"))


@pytest.fixture
def complex_md(complex_data: dict) -> str:
    return render_json_to_markdown(complex_data, title="Test Document")


# ─── Structure tests ─────────────────────────────────────────────────────────


class TestMarkdownStructure:
    """The output should be well-formed Markdown."""

    def test_starts_with_title(self, complex_md: str):
        assert complex_md.startswith("# Test Document")

    def test_no_title_option(self, complex_data: dict):
        md = render_json_to_markdown(complex_data, title=None)
        assert not md.startswith("#")

    def test_accepts_raw_json_string(self):
        raw = '{"hello": "world"}'
        md = render_json_to_markdown(raw)
        assert "hello" in md
        assert "world" in md


# ─── Dollar sign tests ──────────────────────────────────────────────────────


class TestDollarSigns:
    """Dollar signs must be backslash-escaped."""

    def test_dollar_escaped_in_values(self, complex_md: str):
        # "$100" should become "\$100" in non-markdown values
        assert "\\$100" in complex_md

    def test_dollar_escaped_in_keys(self, complex_md: str):
        # "dollar$signs" key should have escaped $
        assert "\\$" in complex_md


# ─── Unicode tests ───────────────────────────────────────────────────────────


class TestUnicode:
    """All unicode characters should pass through Markdown unchanged."""

    def test_emoji_preserved(self, complex_md: str):
        assert "🌍" in complex_md
        assert "🎉" in complex_md
        assert "🏊" in complex_md

    def test_cjk_preserved(self, complex_md: str):
        assert "日本語" in complex_md

    def test_accented_chars(self, complex_md: str):
        assert "Héllo" in complex_md


# ─── Embedded markdown tests ────────────────────────────────────────────────


class TestEmbeddedMarkdown:
    """Markdown content in values should be passed as-is."""

    def test_markdown_headings_preserved(self, complex_md: str):
        # multiline_md_value contains "# Title"
        assert "# Title" in complex_md

    def test_markdown_list_preserved(self, complex_md: str):
        assert "- item 1" in complex_md
        assert "- item 2" in complex_md

    def test_markdown_code_block_preserved(self, complex_md: str):
        assert "```python" in complex_md
        assert "print('hello')" in complex_md

    def test_markdown_link_preserved(self, complex_md: str):
        # markdown_rich_value contains "[link](https://example.com)"
        assert "[link](https://example.com)" in complex_md


# ─── Special characters in keys ─────────────────────────────────────────────


class TestSpecialCharKeys:
    """Keys with special MD characters should be escaped."""

    def test_pipe_in_key_escaped(self, complex_md: str):
        assert "\\|" in complex_md

    def test_backslash_in_key_escaped(self, complex_md: str):
        assert "\\\\" in complex_md


# ─── Nested structures ──────────────────────────────────────────────────────


class TestNestedStructures:
    """Nested objects and arrays should produce indented output."""

    def test_deep_value(self, complex_md: str):
        assert "deep value 🏊" in complex_md

    def test_array_items(self, complex_md: str):
        assert "string" in complex_md


# ─── Empty values ────────────────────────────────────────────────────────────


class TestEmptyValues:
    """Empty strings, arrays, and objects should render gracefully."""

    def test_empty_object(self, complex_md: str):
        assert "empty object" in complex_md

    def test_empty_array(self, complex_md: str):
        assert "empty array" in complex_md


# ─── Primitive types ────────────────────────────────────────────────────────


class TestPrimitiveTypes:
    """Numbers, booleans, and null should render as inline code."""

    def test_null_rendered(self, complex_md: str):
        assert "`null`" in complex_md

    def test_boolean_true(self, complex_md: str):
        assert "`true`" in complex_md

    def test_boolean_false(self, complex_md: str):
        assert "`false`" in complex_md

    def test_numbers(self, complex_md: str):
        assert "`3.14159`" in complex_md
        assert "`42`" in complex_md
