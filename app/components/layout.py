from __future__ import annotations

from pathlib import Path
import streamlit as st
import tomllib


def _load_css(path: str = "style/style.css") -> None:
    css_path = Path(path)
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def _load_nav(path: str = "components/nav.toml") -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def layout(page_title: str) -> None:
    st.set_page_config(page_title=page_title, layout="wide", page_icon="🔮")

    # Carregar CSS
    _load_css()

    # Carregar navegação
    cfg = _load_nav()

    for item in cfg.get("items", []):
        t = item.get("type")
        if t == "section":
            st.sidebar.markdown(f"### {item['label']}")
            continue

        icon = item.get("icon", "")
        label = item.get("label", "")
        full_label = f"{icon} {label}".strip()

        if t == "page":
            st.sidebar.page_link(item["path"], label=full_label)
        elif t == "link":
            st.sidebar.page_link(item["url"], label=full_label)
