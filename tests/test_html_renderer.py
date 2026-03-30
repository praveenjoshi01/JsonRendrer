"""
Tests for the JSON → HTML renderer.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from json_renderer.html_renderer import render_json_to_html

FIXTURES_DIR = Path(__file__).parent / "fixtures"
COMPLEX_JSON = FIXTURES_DIR / "complex.json"


@pytest.fixture
def complex_data() -> dict:
    return json.loads(COMPLEX_JSON.read_text(encoding="utf-8"))


@pytest.fixture
def complex_html(complex_data: dict) -> str:
    return render_json_to_html(complex_data, title="Test")


# ─── Structure tests ─────────────────────────────────────────────────────────


class TestHTMLStructure:
    """The output should be a well-formed HTML document."""

    def test_is_full_document(self, complex_html: str):
        assert complex_html.startswith("<!DOCTYPE html>")
        assert "</html>" in complex_html

    def test_has_title(self, complex_html: str):
        assert "<title>Test</title>" in complex_html

    def test_has_style_block(self, complex_html: str):
        assert "<style>" in complex_html

    def test_accepts_raw_json_string(self):
        raw = '{"hello": "world"}'
        html = render_json_to_html(raw)
        assert "hello" in html
        assert "world" in html


# ─── XSS / injection tests ──────────────────────────────────────────────────


class TestXSSProtection:
    """Script tags and event handlers must be neutralised."""

    def test_script_tag_stripped(self, complex_html: str):
        # Raw <script> tags must never appear — entity-escaped or stripped
        assert "<script>" not in complex_html
        assert "</script>" not in complex_html

    def test_html_entities_escaped(self, complex_html: str):
        # angle brackets in non-markdown text must be escaped
        assert "5 &lt; 10 &amp;&amp; 10 &gt; 5" in complex_html


# ─── Dollar sign tests ──────────────────────────────────────────────────────


class TestDollarSigns:
    """Dollar signs must be entity-escaped to prevent LaTeX interpretation."""

    def test_single_dollar_escaped(self, complex_html: str):
        # "$100" should become "&#36;100"
        assert "&#36;100" in complex_html

    def test_raw_dollar_not_present_in_text(self, complex_html: str):
        # No bare $ in text nodes (it's ok inside CSS / attributes)
        # Check the specific test value
        assert "&#36;5" in complex_html  # Price is $5


# ─── Unicode tests ───────────────────────────────────────────────────────────


class TestUnicode:
    """All unicode characters should survive rendering."""

    def test_emoji_preserved(self, complex_html: str):
        assert "🌍" in complex_html
        assert "🎉" in complex_html
        assert "🏊" in complex_html

    def test_cjk_preserved(self, complex_html: str):
        assert "日本語" in complex_html

    def test_accented_chars_preserved(self, complex_html: str):
        assert "Héllo" in complex_html
        assert "ñ" in complex_html

    def test_zwj_family_emoji(self, complex_html: str):
        assert "👨\u200d👩\u200d👧\u200d👦" in complex_html

    def test_rtl_text(self, complex_html: str):
        assert "مرحبا" in complex_html


# ─── Nested structure tests ─────────────────────────────────────────────────


class TestNestedStructures:
    """Deeply nested objects and arrays should render without errors."""

    def test_deep_nesting(self, complex_html: str):
        assert "deep value 🏊" in complex_html

    def test_mixed_array_renders(self, complex_html: str):
        assert "42" in complex_html
        assert "string" in complex_html


# ─── Empty value tests ──────────────────────────────────────────────────────


class TestEmptyValues:
    """Empty strings, arrays, and objects should render gracefully."""

    def test_empty_object(self, complex_html: str):
        assert "{ }" in complex_html

    def test_empty_array(self, complex_html: str):
        assert "[ ]" in complex_html


# ─── Markdown in values tests ───────────────────────────────────────────────


class TestEmbeddedMarkdown:
    """Values containing markdown should be rendered as HTML safely."""

    def test_markdown_heading_rendered(self, complex_html: str):
        # The multiline_md_value has "# Title" which should become <h1>
        assert "md-rendered" in complex_html

    def test_markdown_list_rendered(self, complex_html: str):
        # The markdown value has list items
        assert "<li>" in complex_html


# ─── Boolean and null tests ─────────────────────────────────────────────────


class TestPrimitiveTypes:
    """Booleans and null should render with proper CSS classes."""

    def test_true_rendered(self, complex_html: str):
        assert 'class="json-bool"' in complex_html
        assert "true" in complex_html

    def test_false_rendered(self, complex_html: str):
        assert "false" in complex_html

    def test_null_rendered(self, complex_html: str):
        assert 'class="json-null"' in complex_html
        assert "null" in complex_html

    def test_numbers(self, complex_html: str):
        assert "3.14159" in complex_html
        assert "42" in complex_html
