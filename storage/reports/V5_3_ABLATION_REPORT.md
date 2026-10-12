# SAP Utilities RAG Retrieval Engine V5.3 — Ablation Analysis Report

## Component Net-Value Contribution Table

| Component | Δ R@5 | Δ R@10 | Δ MRR | Δ Doc R@10 | Δ Mean Lat (ms) | Net Status |
|---|---|---|---|---|---|---|
| RRF 50/50 Backbone | +0.0366 | -0.0250 | +0.0549 | +0.0200 | -59.9 ms | KEPT (POSITIVE NET VALUE) |
| Top-1 Protection + Stability Margin | +0.0000 | +0.0000 | +0.0280 | +0.0000 | +0.5 ms | KEPT (HIGH MRR VALUE) |
| Document Diversification (`max=2`) | -0.0266 | -0.0317 | -0.0186 | -0.0467 | +150.0 ms | REMOVED (NEGATIVE NET VALUE) |
| Technical Phrase & Generic Title Shield | +0.0000 | +0.0100 | +0.0150 | +0.0100 | +1.2 ms | KEPT (POSITIVE NET VALUE) |
