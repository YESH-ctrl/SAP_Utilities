"""
Streamlit component for rendering conversation message history and assistant responses.
"""

import streamlit as st
from typing import List, Dict, Any
from frontend.components.sources import render_sources

def render_chat_history(show_debug_scores: bool = False):
    """
    Render all user and assistant messages stored in session state.
    """
    messages: List[Dict[str, Any]] = st.session_state.get("messages", [])

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        sources = msg.get("sources", [])
        metadata = msg.get("metadata", {})

        with st.chat_message(role):
            st.markdown(content)

            # Display latency breakdown for assistant responses (Section 15)
            if role == "assistant" and metadata:
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

            # Display sources if present
            if role == "assistant" and sources:
                render_sources(sources, show_debug_scores=show_debug_scores)
