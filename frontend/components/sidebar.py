"""
Streamlit component for rendering the Chatbot Sidebar.
"""

import uuid
import streamlit as st
from typing import Dict, Any
from frontend.config import RETRIEVAL_VERSION, DEFAULT_TOP_K
from frontend.api_client import RAGAPIClient

def render_sidebar(api_client: RAGAPIClient) -> Dict[str, Any]:
    """
    Render sidebar controls: New Chat, Conversation ID, Health Status, Retrieval Version, Settings.
    """
    with st.sidebar:
        st.title("⚡ SAP Utilities RAG")
        st.caption(f"Engine Release: **V{RETRIEVAL_VERSION}**")
        st.divider()

        # 1. New Chat Action
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            st.session_state["messages"] = []
            st.session_state["conversation_id"] = str(uuid.uuid4())
            st.rerun()

        # 2. Conversation ID Display
        conv_id = st.session_state.get("conversation_id", "Not Started")
        st.markdown(f"**Session ID:**")
        st.code(conv_id[:18] + "..." if len(conv_id) > 18 else conv_id, language="text")

        st.divider()

        # 3. Backend Health Status Badge
        st.markdown("### 🖥️ **Backend Status**")
        health = api_client.health()
        status_code = health.get("status", "unknown")

        if status_code == "healthy":
            chunk_cnt = health.get("database_chunks", 0)
            vector_cnt = health.get("database_vectors", 0)
            st.success(f"● **Backend Online**\nV{RETRIEVAL_VERSION}\n{vector_cnt:,} vectors ({chunk_cnt:,} chunks)")
        elif status_code == "unhealthy":
            st.warning(f"⚠️ **Backend Issue**\n{health.get('error')}")
        else:
            st.error(f"🔴 **Backend Offline**\nCannot connect to FastAPI server.")

        st.divider()

        # 4. Settings & Debug Options
        st.markdown("### ⚙️ **Settings**")
        top_k = st.slider("Top K Retrieved Chunks", min_value=1, max_value=25, value=DEFAULT_TOP_K, step=1)
        show_debug = st.checkbox("Show Technical Retrieval Scores", value=False)

        st.divider()
        st.caption("🔒 Grounded on 29 SAP Utilities Documentation Sources (6,689 vectors)")

        return {
            "top_k": top_k,
            "show_debug": show_debug
        }
