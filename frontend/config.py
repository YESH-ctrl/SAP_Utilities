"""
Configuration settings for SAP Utilities RAG Streamlit Frontend.
Centralizes base URLs, timeouts, and frontend constants.
"""

import os

# Backend API configuration
RAG_API_URL = os.getenv("RAG_API_URL", "http://localhost:8000").rstrip("/")
CHAT_API_TIMEOUT = float(os.getenv("CHAT_API_TIMEOUT", "60.0"))
MAX_CONVERSATION_MESSAGES = int(os.getenv("MAX_CONVERSATION_MESSAGES", "20"))

# Application Metadata
APP_TITLE = "SAP Utilities AI Assistant"
APP_SUBTITLE = "Grounded Conversational RAG System for SAP Utilities Documentation"
RETRIEVAL_VERSION = "5.5.1"
DEFAULT_TOP_K = 10
