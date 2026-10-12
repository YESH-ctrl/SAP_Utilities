"""
Streamlit component for displaying grounded SAP Utilities source citations cleanly.
"""

import streamlit as st
from typing import List, Dict, Any

def render_sources(sources: List[Dict[str, Any]], show_debug_scores: bool = False):
    """
    Render retrieved SAP Utilities documentation sources in a clean, user-friendly layout.
    Hides raw mathematical retrieval scores by default while making document title, ID,
    breadcrumb, and SAP documentation URL primary.
    """
    if not sources:
        return

    st.markdown("---")
    st.markdown("##### 📚 **Retrieved SAP Documentation Sources**")

    with st.expander(f"View {len(sources)} Supporting SAP Documentation Source(s)", expanded=False):
        for idx, src in enumerate(sources, 1):
            title = src.get("title") or f"SAP Documentation {src.get('document_id', idx)}"
            doc_id = src.get("document_id", "N/A")
            url = src.get("url")
            breadcrumb = src.get("breadcrumb", "")
            excerpt = src.get("excerpt", "")
            score = src.get("score")

            st.markdown(f"**{idx}. {title}**")
            st.caption(f"Doc ID: `{doc_id}`" + (f" | Path: *{breadcrumb}*" if breadcrumb else ""))

            if excerpt:
                st.markdown(f"> *{excerpt}*")

            if url and url != "N/A":
                st.markdown(f"[🔗 Open SAP Documentation]({url})")

            # Technical scores hidden behind optional debug mode (Section 14)
            if show_debug_scores and score is not None:
                st.caption(f"⚙️ *Debug Retrieval Score:* `{score}`")

            if idx < len(sources):
                st.divider()
