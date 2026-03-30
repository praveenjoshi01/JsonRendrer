"""
JsonRenderer — Streamlit Demo App

An interactive playground for the JSON → HTML and JSON → Markdown renderers.
Upload a JSON file or paste one, toggle the output format, and preview live.
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from json_renderer.html_renderer import render_json_to_html
from json_renderer.md_renderer import render_json_to_markdown

# ─── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="JsonRenderer Demo",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    .stApp {
        font-family: 'Inter', sans-serif;
    }

    .main-title {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #818cf8, #a78bfa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 2rem;
    }

    .stat-card {
        background: #1a1d2e;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        text-align: center;
    }

    .stat-number {
        font-size: 1.8rem;
        font-weight: 700;
        color: #818cf8;
        font-family: 'JetBrains Mono', monospace;
    }

    .stat-label {
        font-size: 0.82rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    div[data-testid="stCodeBlock"] {
        font-family: 'JetBrains Mono', monospace;
    }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.markdown("---")

    output_format = st.radio(
        "Output Format",
        ["HTML", "Markdown"],
        index=0,
        help="Choose the rendering output format",
    )

    doc_title = st.text_input(
        "Document Title",
        value="JSON Document",
        help="Title for the rendered output",
    )

    st.markdown("---")
    st.markdown("### 📂 Quick Load")

    complex_json_path = Path(__file__).parent / "tests" / "fixtures" / "complex.json"
    if complex_json_path.exists():
        if st.button("🧪 Load Complex Test JSON", use_container_width=True):
            st.session_state["json_input"] = complex_json_path.read_text(encoding="utf-8")
            st.rerun()

    st.markdown("---")
    st.markdown(
        '<div style="color: #64748b; font-size: 0.8rem; text-align: center;">'
        "JsonRenderer v1.0.0<br>Built with ❤️"
        "</div>",
        unsafe_allow_html=True,
    )

# ─── Header ──────────────────────────────────────────────────────────────────

st.markdown('<div class="main-title">🎨 JsonRenderer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">'
    "Safely render any JSON to HTML or Markdown — unicode, dollar signs, embedded markdown, XSS payloads, and all."
    "</div>",
    unsafe_allow_html=True,
)

# ─── Input area ──────────────────────────────────────────────────────────────

col_upload, col_paste = st.columns([1, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "Upload a JSON file",
        type=["json"],
        help="Drag & drop or click to browse",
    )

json_text = ""

if uploaded_file is not None:
    json_text = uploaded_file.getvalue().decode("utf-8")
    st.session_state["json_input"] = json_text

default_json = st.session_state.get("json_input", '{\n  "greeting": "Hello, World! 🌍",\n  "price": "$9.99",\n  "note": "Use **bold** for emphasis"\n}')

with col_paste:
    json_text = st.text_area(
        "Or paste JSON here",
        value=default_json,
        height=250,
        help="Paste any JSON — we handle the edge cases",
    )

# ─── Parse & Render ─────────────────────────────────────────────────────────

if json_text.strip():
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        st.error(f"**Invalid JSON:** {e}")
        st.stop()

    # ── Stats row ────────────────────────────────────────────────────────
    def count_keys(d, depth=0):
        keys, max_d = 0, depth
        if isinstance(d, dict):
            keys += len(d)
            for v in d.values():
                k, md = count_keys(v, depth + 1)
                keys += k
                max_d = max(max_d, md)
        elif isinstance(d, list):
            for v in d:
                k, md = count_keys(v, depth + 1)
                keys += k
                max_d = max(max_d, md)
        return keys, max_d

    total_keys, max_depth = count_keys(data)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="stat-card"><div class="stat-number">{total_keys}</div>'
            f'<div class="stat-label">Total Keys</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="stat-card"><div class="stat-number">{max_depth}</div>'
            f'<div class="stat-label">Max Depth</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="stat-card"><div class="stat-number">{len(json_text):,}</div>'
            f'<div class="stat-label">Characters</div></div>',
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f'<div class="stat-card"><div class="stat-number">{output_format}</div>'
            f'<div class="stat-label">Output Mode</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Render ───────────────────────────────────────────────────────────

    if output_format == "HTML":
        rendered = render_json_to_html(data, title=doc_title)

        tab_preview, tab_source = st.tabs(["👁️ Preview", "📄 Source"])

        with tab_preview:
            components.html(rendered, height=700, scrolling=True)

        with tab_source:
            st.code(rendered, language="html", line_numbers=True)

        st.download_button(
            "⬇️ Download HTML",
            data=rendered,
            file_name="output.html",
            mime="text/html",
            use_container_width=True,
        )

    else:
        rendered = render_json_to_markdown(data, title=doc_title)

        tab_preview, tab_source = st.tabs(["👁️ Preview", "📄 Source"])

        with tab_preview:
            st.markdown(rendered)

        with tab_source:
            st.code(rendered, language="markdown", line_numbers=True)

        st.download_button(
            "⬇️ Download Markdown",
            data=rendered,
            file_name="output.md",
            mime="text/markdown",
            use_container_width=True,
        )

else:
    st.info("👆 Upload a JSON file or paste JSON above to get started.")
