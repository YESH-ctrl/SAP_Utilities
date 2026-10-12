"""
SAP Utilities RAG Chatbot - Streamlit Python Frontend.
Provides a ChatGPT-style conversational UI for SAP Utilities documentation RAG.
"""

import sys
import os
import uuid
import streamlit as st

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from frontend.config import APP_TITLE, APP_SUBTITLE, RETRIEVAL_VERSION
from frontend.api_client import RAGAPIClient
from frontend.components.sidebar import render_sidebar
from frontend.components.chat import render_chat_history
from frontend.components.sources import render_sources

# Streamlit Page Configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Sleek ChatGPT-style modern layout)
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 950px;
    }
    .stChatMessage {
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
    }
    .stSidebar {
        background-color: #0e1117;
    }
    header[data-testid="stHeader"] {
        background-color: rgba(0, 0, 0, 0);
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "api_client" not in st.session_state:
    st.session_state["api_client"] = RAGAPIClient()

api_client: RAGAPIClient = st.session_state["api_client"]

# Render Sidebar & Get Settings
settings = render_sidebar(api_client)
top_k = settings.get("top_k", 10)
show_debug = settings.get("show_debug", False)

# Main Application Header
st.title(f"⚡ {APP_TITLE}")
st.caption(f"{APP_SUBTITLE} (Engine Version V{RETRIEVAL_VERSION})")
st.divider()

# Render Message History
render_chat_history(show_debug_scores=show_debug)

# User Input Box
user_input = st.chat_input("Ask about SAP Utilities (e.g., How do I perform a reconnection?)...")

if user_input:
    # 1. Display user message immediately
    st.session_state["messages"].append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Call backend chat API with loader
    with st.chat_message("assistant"):
        with st.spinner("Retrieving SAP Utilities documentation & generating answer..."):
            response = api_client.chat(
                message=user_input,
                conversation_id=st.session_state["conversation_id"],
                top_k=top_k
            )

        if "error" in response:
            error_msg = response["error"]
            st.error(f"⚠️ **Error:** {error_msg}")
            st.session_state["messages"].append({
                "role": "assistant",
                "content": f"⚠️ **Error:** {error_msg}"
            })
        else:
            msg_obj = response.get("message", {})
            content = msg_obj.get("content", "")
            sources = response.get("sources", [])
            metadata = response.get("metadata", {})

            # Render response content
            st.markdown(content)

            # Render latency metadata breakdown
            ret_lat = metadata.get("retrieval_latency_ms")
            gen_lat = metadata.get("generation_latency_ms") or metadata.get("gemini_generation_ms") or metadata.get("llm_latency_ms")
            tot_lat = metadata.get("total_latency_ms")
            model_used = metadata.get("model")

            latency_str = []
            if ret_lat is not None:
                latency_str.append(f"Retrieval: {ret_lat:.0f} ms")
            if gen_lat is not None:
                latency_str.append(f"Generation: {gen_lat:.0f} ms")
            if tot_lat is not None:
                latency_str.append(f"Total: {tot_lat:.0f} ms")

            if latency_str:
                st.caption(f"⏱️ *Latency Breakdown — {' | '.join(latency_str)}*" + (f" (*Model: {model_used}*)" if model_used else ""))

            # Render sources
            if sources:
                render_sources(sources, show_debug_scores=show_debug)

            # Update session state with assistant response
            st.session_state["messages"].append({
                "role": "assistant",
                "content": content,
                "sources": sources,
                "metadata": metadata
            })
