"""
Metrics calculation module for semantic chunk statistics:
- Token count distribution (min, p25, median, p75, p95, max, mean)
- Token size brackets (<100, 100-300, 300-500, 500-800, 800-900, >900)
- Source coverage statistics
"""

import math
from typing import List, Dict, Any

class ChunkMetricsCalculator:
    """
    Computes statistical metrics and token size distributions over chunk datasets.
    """

    @classmethod
    def compute_metrics(cls, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not chunks:
            return {
                "total_chunks": 0,
                "token_stats": {"min": 0, "p25": 0, "median": 0, "p75": 0, "p95": 0, "max": 0, "mean": 0},
                "brackets": {"<100": 0, "100-300": 0, "300-500": 0, "500-800": 0, "800-900": 0, ">900": 0}
            }

        token_counts = sorted([chk.get("token_count", 0) for chk in chunks])
        n = len(token_counts)

        def percentile(p: float) -> float:
            idx = (n - 1) * p
            low = math.floor(idx)
            high = math.ceil(idx)
            if low == high:
                return float(token_counts[int(idx)])
            return token_counts[low] * (high - idx) + token_counts[high] * (idx - low)

        min_val = token_counts[0]
        max_val = token_counts[-1]
        mean_val = sum(token_counts) / n
        p25_val = percentile(0.25)
        median_val = percentile(0.50)
        p75_val = percentile(0.75)
        p95_val = percentile(0.95)

        brackets = {
            "<100": sum(1 for t in token_counts if t < 100),
            "100-300": sum(1 for t in token_counts if 100 <= t < 300),
            "300-500": sum(1 for t in token_counts if 300 <= t < 500),
            "500-800": sum(1 for t in token_counts if 500 <= t <= 800),
            "800-900": sum(1 for t in token_counts if 800 < t <= 900),
            ">900": sum(1 for t in token_counts if t > 900),
        }

        return {
            "total_chunks": n,
            "token_stats": {
                "min": int(min_val),
                "p25": round(p25_val, 1),
                "median": round(median_val, 1),
                "p75": round(p75_val, 1),
                "p95": round(p95_val, 1),
                "max": int(max_val),
                "mean": round(mean_val, 1)
            },
            "brackets": brackets
        }
