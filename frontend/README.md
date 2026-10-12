# SAP Utilities AI Help Assistant Web UI (V5.5.1)

An enterprise-grade, modern React + TypeScript web application built for the **SAP Utilities RAG Retrieval Engine**. Grounded directly in SAP Help Portal documentation, providing dense/lexical hybrid retrieval, reciprocal rank fusion (RRF), hierarchy-aware source recovery (H1), citation inspection, evaluation metrics, and system health monitoring.

---

## 🌟 Architecture & Key Features

- **Grounded AI Assistant (`/chat`)**: Multi-turn SAP Utilities documentation Q&A with Markdown rendering, inline citation badges, right-side sources panel, and detailed source drawers.
- **Documentation Search (`/search`)**: Dedicated semantic vector and BM25 lexical search interface with score breakdown and category filtering.
- **Retrieval Pipeline Inspector (`/retrieval`)**: Live execution trace of the RAG engine showing Dense Retrieval, Lexical Retrieval, RRF Fusion, H1 Recovery, and Candidate Ranking.
- **Evaluation Dashboard (`/evaluation`)**: Visualizes V5.5 benchmark performance metrics (Recall@5/10/20, MRR, NDCG@10, P50/P95/P99 latency) and retrieval failure diagnostics.
- **System Health Telemetry (`/health`)**: Real-time operational monitoring for FastAPI backend, PostgreSQL, pgvector, Gemini embedding, and LLM services.
- **Enterprise Design System**: SAP-inspired color palette (`#005A9E`, `#0A6ED1`, `#0A1B2A`), light/dark mode support, responsive layout, and Developer Diagnostic Mode.

---

## 🚀 Quick Start

### 1. Requirements
- **Node.js**: v18.0.0+
- **Python**: 3.10+ (for running FastAPI backend on `http://localhost:8000`)

### 2. Environment Configuration
Create a `.env` file inside `frontend/`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK_DATA=false
```

### 3. Installation
Navigate to the `frontend/` directory and install node modules:

```bash
cd frontend
npm install
```

### 4. Running Development Server
Start Vite dev server on port `5173`:

```bash
npm run dev
```

The application will be available at: `http://localhost:5173`

---

## ⚡ Backend Integration

The Web UI connects directly to the FastAPI server running `main.py`.

### Registered FastAPI Endpoints consumed:
- `POST /api/v1/chat` -> AI Assistant turn with citations & metadata.
- `POST /api/v1/retrieval/query` -> Documentation search.
- `GET /api/v1/evaluation` -> Real V5.5 benchmark metrics & golden test dataset.
- `GET /api/v1/sources` & `GET /api/v1/sources/{id}` -> Source hierarchy & details.
- `GET /api/v1/health` -> Microservice health telemetry.

---

## 🛠️ Production Build

To create an optimized production build:

```bash
npm run build
```

To preview the production bundle locally:

```bash
npm run preview
```

---

## 📂 Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── router.tsx          # React Router route definitions
│   │   └── providers.tsx       # TanStack Query client provider
│   │
│   ├── components/
│   │   ├── chat/               # ChatInput, ChatMessage, Citation, ExamplePrompts
│   │   ├── sources/            # SourcesPanel, SourceCard, SourceDrawer
│   │   ├── search/             # SearchBar, SearchResultCard
│   │   ├── retrieval/          # PipelineVisualizer, CandidateTable
│   │   ├── evaluation/         # MetricGrid, QueryEvaluationTable, FailureAnalysis
│   │   ├── health/             # SystemHealthGrid
│   │   └── layout/             # AppShell, Sidebar, Topbar
│   │
│   ├── pages/
│   │   ├── ChatPage.tsx
│   │   ├── SearchPage.tsx
│   │   ├── EvaluationPage.tsx
│   │   ├── RetrievalInspectorPage.tsx
│   │   └── HealthPage.tsx
│   │
│   ├── services/
│   │   ├── api.ts              # Centralized fetch client
│   │   ├── chatApi.ts
│   │   ├── searchApi.ts
│   │   ├── evaluationApi.ts
│   │   ├── sourcesApi.ts
│   │   ├── healthApi.ts
│   │   └── mockApi.ts          # Isolated dev mock adapter
│   │
│   ├── hooks/
│   │   ├── useChat.ts
│   │   ├── useSearch.ts
│   │   ├── useEvaluation.ts
│   │   ├── useSources.ts
│   │   └── useHealth.ts
│   │
│   ├── types/
│   │   ├── chat.ts
│   │   ├── search.ts
│   │   ├── retrieval.ts
│   │   ├── evaluation.ts
│   │   └── health.ts
│   │
│   └── lib/
│       ├── constants.ts
│       └── utils.ts
│
├── package.json
├── tailwind.config.js
├── tsconfig.json
├── vite.config.ts
└── README.md
```
