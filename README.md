# SAP Utilities RAG System — V5.5.1 Gemini Answer Generation Layer

Enterprise-grade, grounded **Retrieval-Augmented Generation (RAG) System** for SAP Utilities documentation.
Combines the validated **V5.5.1 Hybrid Retrieval Engine** (Dense + Lexical + RRF + Entity Protection + Hierarchy Recovery) with a grounded **Google Gemini LLM Answer Generation Layer** using official `google-genai` SDK.

---

## 🏗️ Architecture

```
User Question
      ↓
FastAPI (`/api/v1/chat`)
      ↓
V5.5.1 Retrieval Engine (Frozen)
      ↓
Retrieved SAP Documentation Chunks
      ↓
Grounding Context Builder (Context Budget: MAX_CONTEXT_CHUNKS & MAX_CONTEXT_CHARACTERS)
      ↓
Google Gemini LLM (`google-genai` SDK)
      ↓
Grounded Natural-Language Answer
      ↓
Backend-Owned Source Attribution List
      ↓
Streamlit UI
```

---

## ⚡ Key Features (V5.5.1 Release)

1. **Frozen V5.5.1 Retrieval Engine**: RRF 50/50, exact entity title protection, selective recovery, and hierarchy recovery. Recall@5 = 0.8783, Recall@10 = 0.9250, MRR = 0.8192 strictly preserved.
2. **Official Google GenAI SDK Integration**: Uses `google-genai` SDK (`from google import genai`) with non-blocking async generation.
3. **Strict Grounding & Anti-Hallucination**: 20-rule system instruction enforcing exact document factual support.
4. **Independent Source Attribution**: Sources are strictly owned by backend retrieval, avoiding LLM citation hallucinations.
5. **Configurable Context Budgeting**: Post-retrieval context truncation (`MAX_CONTEXT_CHUNKS=10`, `MAX_CONTEXT_CHARACTERS=12000`) without modifying retrieval candidates.
6. **Bounded Conversation History**: Session memory limited to `MAX_CONVERSATION_MESSAGES=20`.
7. **Detailed Latency Instrumentation**: Seperate tracking for retrieval, context building, LLM generation, and total latency.
8. **Graceful Fallbacks**: If Gemini API key is missing or API errors occur, sources are preserved and a clean fallback answer is displayed.

---

## 🚀 Quick Setup & Configuration

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables (`.env`)
Copy `.env.example` to `.env`:

```env
# Supabase Database Credentials
SUPABASE_DB_HOST=db.zmruzdoeslwpccppejjk.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your_password

# Google Gemini API Configuration
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0.2
GEMINI_MAX_OUTPUT_TOKENS=2048

# Grounded Context Budget Configuration
MAX_CONVERSATION_MESSAGES=20
MAX_CONTEXT_CHUNKS=10
MAX_CONTEXT_CHARACTERS=12000
```

> **Security Note:** Set `GEMINI_API_KEY` in environment or `.env` file ONLY. Never commit `.env` to Git. `.gitignore` is pre-configured to block secrets.

---

## 🖥️ Running the Application

### 1. Start FastAPI Backend Server
```bash
python main.py
```
*Server starts on `http://localhost:8000`. API Docs available at `http://localhost:8000/docs`.*

### 2. Start Streamlit Conversational UI
```bash
streamlit run frontend/app.py
```
*App opens automatically at `http://localhost:8501`.*

---

## 🧪 Testing & Validation

### 1. Unit Test Suite (Gemini Service & Chat API)
Run all unit tests using mocks (no external API calls required):
```bash
pytest tests/test_gemini_service.py tests/test_chat_api.py -v
```

### 2. Live Integration Test
Run live test with configured Gemini API key:
```bash
python scripts/test_gemini_live.py
```

### 3. Retrieval Engine Regression Benchmark
Verify frozen V5.5.1 metrics (Recall@5=0.8783, Recall@10=0.9250, MRR=0.8192):
```bash
python evaluation/test_v5_5_target_queries.py
```

---

## 🔒 Security Best Practices

- `GEMINI_API_KEY` is backend-only and never exposed to Streamlit or frontend JS.
- API Key is excluded from all API response payloads and backend logs.
- `.env` and `.env.*` files are explicitly ignored in `.gitignore`.

---

## 🛠️ Troubleshooting

- **Gemini API Key missing warning on startup**: The backend will run in fallback synthesizer mode. Provide `GEMINI_API_KEY` in `.env` to enable live Gemini generation.
- **503 / Rate Limit Errors**: System automatically falls back to clean error message while keeping retrieved SAP documentation sources intact.
