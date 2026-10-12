# INTEGRATION ARCHITECTURE — SAP UTILITIES RAG V5.5.1 CHATBOT & API

## 1. System Architecture Diagram

```
                    ┌────────────────────────┐
                    │      Streamlit UI      │
                    │   (Python Frontend)    │
                    └───────────┬────────────┘
                                │
                                │ HTTP (JSON)
                                ▼
                    ┌────────────────────────┐
                    │        FastAPI         │
                    │      (API Layer)       │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │      Chat Service      │
                    │    (Orchestration)     │
                    └───────────┬────────────┘
                                │
                  ┌─────────────┴─────────────┐
                  ▼                           ▼
        ┌───────────────────┐       ┌───────────────────┐
        │  V5.5.1 RAG       │       │  LLM Generation   │
        │  Retrieval Engine │       │  Service          │
        └─────────┬─────────┘       └─────────┬─────────┘
                  │                           │
                  ▼                           │
        ┌───────────────────┐                 │
        │  PostgreSQL +     │◄────────────────┘
        │  pgvector         │
        └───────────────────┘
```

---

## 2. Component Design & Responsibilities

### 2.1 Streamlit Frontend (`frontend/`)
- **`app.py`**: Main application interface providing ChatGPT-style user experience.
- **`api_client.py`**: Dedicated `RAGAPIClient` wrapper handling HTTP calls to FastAPI with timeouts, error parsing, and central configuration.
- **`components/sidebar.py`**: Controls for starting new conversations, viewing session IDs, checking backend connectivity badges, and tuning top_k chunk sliders.
- **`components/chat.py`**: Handles rendering message bubbles, thinking/loading spinners, and response metadata tags.
- **`components/sources.py`**: Renders expandable SAP Utilities documentation sources with title, document ID, score, URL, and contextual excerpts.

> **Frontend Isolation**: Streamlit code has zero direct database credentials, zero direct PostgreSQL access, zero embedding logic, and zero retrieval calculations. All interactions pass through FastAPI HTTP routes.

### 2.2 FastAPI API Layer (`main.py`, `sap_rag/api/`)
- **`main.py`**: Entry point managing `DatabasePool` lifespan events, CORS middleware, and router registration.
- **`sap_rag/api/retrieval_router.py`**: Exposes `/api/v1/retrieval/query` and `/api/v1/retrieval/health`.
- **`sap_rag/api/chat_router.py`**: Exposes `/api/v1/chat`.

### 2.3 Chat Service Orchestrator (`sap_rag/chat/service.py`)
- Manages bounded in-memory session history via `ConversationStore` (bounded by `MAX_CONVERSATION_MESSAGES=20`).
- Coordinates V5.5.1 Retrieval Engine execution and LLM Grounded Answer Generation.
- Extracts and deduplicates unique SAP Utilities source citations.

### 2.4 Grounded LLM Generation Service (`sap_rag/llm/service.py`)
- Provider abstraction supporting Google Gemini, OpenAI, or a deterministic grounded synthesizer fallback.
- Enforces strict system instructions requiring factual grounding in retrieved SAP Utilities documentation.
- Safe no-context fallback: `"I couldn't find sufficient supporting SAP Utilities documentation in the retrieved knowledge base to answer this confidently."`

---

## 3. API Contracts

### 3.1 Retrieval Endpoint
- **URL**: `POST /api/v1/retrieval/query` (Alias: `POST /api/v1/retrieval/search`)
- **Request**:
```json
{
  "query": "How do I perform a reconnection?",
  "top_k": 10
}
```
- **Response**:
```json
{
  "query": "How do I perform a reconnection?",
  "processed_query": { ... },
  "results": [
    {
      "rank": 1,
      "chunk_id": 2691,
      "document_id": 2691,
      "source_id": 29,
      "title": "Reconnection Entry",
      "url": "https://help.sap.com/...",
      "breadcrumb": "IS-U > Customer Service > Disconnection/Reconnection",
      "content": "...",
      "score": 0.0372,
      "retrieval_method": "hybrid_rrf",
      "scores_breakdown": { ... }
    }
  ],
  "formatted_context": "...",
  "metadata": {
    "retrieval_version": "5.5.1",
    "total_latency_ms": 120.5
  }
}
```

### 3.2 Chat Endpoint
- **URL**: `POST /api/v1/chat`
- **Request**:
```json
{
  "message": "How do I perform a reconnection?",
  "conversation_id": "optional-uuid-v4",
  "top_k": 10
}
```
- **Response**:
```json
{
  "conversation_id": "58c02bf8-9522-45d8-843e-bff4ccf34d1e",
  "message": {
    "role": "assistant",
    "content": "Based on the retrieved SAP Utilities documentation: ..."
  },
  "sources": [
    {
      "rank": 1,
      "title": "Reconnection Entry",
      "document_id": 2691,
      "source_id": 29,
      "url": "https://help.sap.com/...",
      "excerpt": "Meter Reading Data During Move In...",
      "score": 0.0372
    }
  ],
  "metadata": {
    "retrieval_version": "5.5.1",
    "retrieval_latency_ms": 1827.67,
    "llm_latency_ms": 0.05,
    "total_latency_ms": 1827.83,
    "candidate_count": 10
  }
}
```

### 3.3 Health Endpoint
- **URL**: `GET /api/v1/retrieval/health`
- **Response**:
```json
{
  "status": "healthy",
  "database_chunks": 6689,
  "database_vectors": 6689,
  "model": "BAAI/bge-m3",
  "dimension": 1024
}
```

---

## 4. Security Model & Secret Management
- **Secret Isolation**: All database passwords (`SUPABASE_DB_PASSWORD`) and LLM API keys (`GEMINI_API_KEY`, `OPENAI_API_KEY`) remain strictly on the FastAPI server environment.
- **CORS Control**: Configurable via `ALLOWED_ORIGINS` environment variable (defaults to `http://localhost:8501,http://127.0.0.1:8501`).
- **Input Sanitization**: Pydantic validation rejects empty, whitespace, or malformed queries.
- **Prompt Injection Defense**: Grounding prompt strictly mandates relying only on supplied context and refusing prompt overrides.

---

## 5. Local Development Instructions

### Backend (FastAPI):
```bash
python main.py
# Server runs on http://localhost:8000
# OpenAPI Docs available at http://localhost:8000/docs
```

### Frontend (Streamlit):
```bash
streamlit run frontend/app.py
# Frontend runs on http://localhost:8501
```

### Running Tests:
```bash
# Unit & Integration Tests:
python -m pytest tests/

# End-to-End Acceptance Test:
python scripts/test_v551_e2e_chatbot.py
```
