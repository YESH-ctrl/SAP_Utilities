# SAP Utilities RAG Retrieval Engine Report

## Architecture
- **Dense Model**: `BAAI/bge-m3` (1024 dims)
- **Vector DB**: Supabase PostgreSQL + pgvector (HNSW cosine similarity index `idx_embeddings_vector_hnsw`)
- **Lexical DB**: PostgreSQL Full-Text Search (`tsvector`, `websearch_to_tsquery`, `ts_rank_cd`)
- **Hybrid Fusion**: Min-Max Score Normalization + Weighted Combination (`0.70` Dense, `0.30` Lexical)
- **Metadata Scoring**: Document title boost (`0.10`), Breadcrumb boost (`0.10`), Technical term boost (`0.05`), Hierarchy boost (`0.05`)
- **Re-ranking**: Second-stage `FastFeatureReranker` comparing query-document interaction
- **Hierarchy Expansion**: Controlled neighbor window expansion (`window=1`)
- **MMR Diversity**: Maximal Marginal Relevance selection (`lambda=0.75`)

## Corpus & Index State
- **Total Chunks**: `6,689`
- **Total Vectors**: `6,689`
- **Embedding Coverage**: `100.0%`
- **Missing Embeddings**: `0`

## Benchmark Evaluation Metrics (50 Test Questions)
| Pipeline Configuration | Recall@5 | Recall@10 | Recall@20 | Precision@5 | Precision@10 | MRR |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `dense_only` | 0.7000 | 0.7400 | 0.7600 | 0.5240 | 0.4820 | 0.6105 |
| `lexical_only` | 0.7933 | 0.8500 | 0.8800 | 0.6080 | 0.5571 | 0.7092 |
| `hybrid` | 0.6950 | 0.7400 | 0.7600 | 0.5480 | 0.4960 | 0.6672 |
| `hybrid_metadata` | 0.6700 | 0.7400 | 0.7600 | 0.5240 | 0.4980 | 0.6564 |
| `hybrid_metadata_rerank` | 0.7900 | 0.8600 | 0.8600 | 0.5800 | 0.5480 | 0.6897 |
| `full_pipeline` | 0.7983 | 0.8600 | 0.8600 | 0.5640 | 0.5600 | 0.7012 |

## Real SAP Utilities Retrieval Traces (20 Sample Queries)
| Query | Top Retrieved Document | Top Chunk ID | Score | Latency (ms) | Target Source Match |
| :--- | :--- | :---: | :---: | :---: | :---: |
| How do I create an installment plan?... | How to Create Sales Contracts for E... | #10167 | 0.3956 | 1039.64ms | `MISMATCH` |
| How does clearing control work for incom... | Clearing Control in Incoming Paymen... | #11754 | 0.6995 | 976.37ms | `MATCH` |
| What is the process for automatic billin... | Automatic Billing... | #9499 | 0.7142 | 1129.05ms | `MATCH` |
| How are meter readings estimated?... | Meter Reading Result... | #6949 | 0.6178 | 647.35ms | `MATCH` |
| What happens during move-in?... | Move-in... | #6045 | 0.5297 | 763.47ms | `MATCH` |
| What happens during move-out?... | Move-Out... | #6072 | 0.5495 | 750.51ms | `MATCH` |
| How does FI-CA dunning work?... | Dunning Procedure... | #12025 | 0.5644 | 1667.12ms | `MATCH` |
| How are incoming payments processed?... | Monitoring Payments... | #11879 | 0.5906 | 853.61ms | `MATCH` |
| What are clearing types in SAP Utilities... | Using Transaction Types for Utiliti... | #10316 | 0.4468 | 1249.83ms | `MISMATCH` |
| How does budget billing work?... | Budget Billing Amounts... | #8791 | 0.6138 | 1045.64ms | `MISMATCH` |
| What master data is required for SAP Uti... | Enterprise Search for Utilities Mas... | #11297 | 0.5908 | 621.71ms | `MISMATCH` |
| How is device management configured for ... | Device Management... | #6094 | 0.5699 | 634.9ms | `MATCH` |
| How to monitor meter reading results?... | Monitoring of Meter Reading Results... | #6598 | 0.782 | 632.61ms | `MISMATCH` |
| What are the details of the estimation p... | Guided Procedure Configuration... | #10054 | 0.3938 | 847.87ms | `MISMATCH` |
| How is meter reading data processed duri... | Meter Reading Data (Move-In)... | #7141 | 0.7147 | 793.1ms | `MATCH` |
| What is the billing procedure in SAP Uti... | Budget Billing Plan Procedure... | #7644 | 0.756 | 696.08ms | `MATCH` |
| How is the invoicing procedure executed?... | Invoicing Procedure... | #10577 | 0.6747 | 809.95ms | `MATCH` |
| How to process budget billing plans?... | Processing Budget Billing Plans... | #7454 | 0.7776 | 692.1ms | `MISMATCH` |
| What is a contract account business obje... | Contract Account... | #11485 | 0.643 | 797.25ms | `MATCH` |
| How to process incoming payments from a ... | Submission of Receivables to Collec... | #12178 | 0.5683 | 931.1ms | `MISMATCH` |

## Verification Summary
- Existing 6,689 chunks: **UNMUTATED**
- Existing 6,689 embeddings: **UNMUTATED**
- Retrieval Engine API Status: **READY**
