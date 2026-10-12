"""
Dedicated API Client for Streamlit Frontend to communicate with FastAPI backend.
Centralizes base URL, headers, timeouts, error handling, and JSON parsing.
"""

import logging
from typing import Dict, Any, Optional
import httpx
from frontend.config import RAG_API_URL, CHAT_API_TIMEOUT

logger = logging.getLogger(__name__)

class RAGAPIClient:
    """
    HTTP API Client for interacting with the SAP Utilities RAG FastAPI backend.
    No direct database or backend secrets are exposed to the frontend.
    """

    def __init__(self, base_url: str = RAG_API_URL, timeout: float = CHAT_API_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health(self) -> Dict[str, Any]:
        """
        Check backend health and database readiness across candidate health endpoints.
        """
        endpoints = [
            f"{self.base_url}/api/v1/retrieval/health",
            f"{self.base_url}/health",
            f"{self.base_url}/api/v1/health"
        ]

        last_status_code = None
        try:
            with httpx.Client(timeout=self.timeout) as client:
                for url in endpoints:
                    try:
                        resp = client.get(url)
                        last_status_code = resp.status_code
                        if resp.status_code == 200:
                            return resp.json()
                    except Exception:
                        continue

                return {
                    "status": "unhealthy",
                    "error": f"Backend returned status code {last_status_code if last_status_code else '404'}"
                }
        except httpx.ConnectError:
            return {
                "status": "offline",
                "error": f"Unable to connect to backend at {self.base_url}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Send a chat question to the RAG backend across candidate chat endpoints.
        """
        endpoints = [
            f"{self.base_url}/api/v1/chat",
            f"{self.base_url}/api/v1/chat/",
            f"{self.base_url}/chat"
        ]
        payload = {
            "message": message,
            "messages": [{"role": "user", "content": message}],
            "conversation_id": conversation_id,
            "top_k": top_k
        }

        last_resp = None
        try:
            with httpx.Client(timeout=self.timeout) as client:
                for url in endpoints:
                    try:
                        resp = client.post(url, json=payload)
                        last_resp = resp
                        if resp.status_code == 200:
                            return resp.json()
                    except Exception:
                        continue

                error_detail = "Unknown backend error"
                if last_resp is not None:
                    try:
                        err_json = last_resp.json()
                        error_detail = err_json.get("detail", str(last_resp.text))
                    except Exception:
                        error_detail = last_resp.text
                    return {
                        "error": f"API Error ({last_resp.status_code}): {error_detail}"
                    }
                return {
                    "error": "API Error (404): Endpoint not found"
                }
        except httpx.ConnectError:
            return {
                "error": f"Cannot reach API backend at {self.base_url}. Please ensure FastAPI is running."
            }
        except httpx.TimeoutException:
            return {
                "error": f"Request to API timed out after {self.timeout}s."
            }
        except Exception as e:
            return {
                "error": f"Unexpected error communicating with API: {str(e)}"
            }

    def retrieve(
        self,
        query: str,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Perform direct retrieval query without chat generation.
        """
        url = f"{self.base_url}/api/v1/retrieval/query"
        payload = {
            "query": query,
            "top_k": top_k
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    return resp.json()
                else:
                    return {"error": f"Retrieval failed with status {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"error": f"Retrieval client error: {str(e)}"}
