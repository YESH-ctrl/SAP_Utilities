# V5.1 Latency & Performance Report

## WARM PROCESS LATENCY (Production Gateway)
| Latency Metric | Measured Value | Target Gate | Status |
| :--- | :---: | :---: | :---: |
| Average Latency | 506.8 ms | < 500.0 ms | `FAILED (Cloud DB RTT)` |
| P50 Latency | 517.6 ms | < 400.0 ms | `FAILED` |
| P95 Latency | 796.4 ms | < 1000.0 ms | `PASSED` |
| P99 Latency | 1021.3 ms | < 1500.0 ms | `PASSED` |
| Query Embedding (Cached) | 0.000 ms | < 1.0 ms | `PASSED` |

## COLD START LATENCY
- **Cold Initialization Total**: `8348.1 ms`
- **Includes**: Database connection pool setup + PyTorch model verification + Tokenizer loading.

## LRU Query Cache Statistics
- Hits: `300` | Misses: `130` | Hit Rate: `69.8%`