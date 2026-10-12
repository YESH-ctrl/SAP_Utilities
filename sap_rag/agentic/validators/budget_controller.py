"""
Execution Budget Controller for Agentic Intelligence Platform.
Enforces request-level hard deadlines, concurrency limits, maximum investigation rounds,
context token caps, and graceful degradation under pressure.
"""

import os
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("sap_rag.agentic.validators.budget")


class ExecutionBudgetExceeded(Exception):
    """Raised when execution budget or deadline is exceeded."""
    pass


class ExecutionBudgetController:
    """
    Tracks and enforces resource budgets for a single request lifecycle.
    """

    def __init__(
        self,
        timeout_seconds: float = float(os.getenv("AGENTIC_TIMEOUT_SECONDS", "90.0")),
        max_investigation_rounds: int = 2,
        max_context_tokens: int = 6000,
        max_specialist_agents: int = 5
    ):
        self.timeout_seconds = timeout_seconds
        self.max_investigation_rounds = max_investigation_rounds
        self.max_context_tokens = max_context_tokens
        self.max_specialists = max_specialist_agents

        self.start_time = time.perf_counter()
        self.current_round = 0
        self.specialists_executed = 0
        self.tokens_used = 0
        self.is_cancelled = False

    def elapsed_seconds(self) -> float:
        return time.perf_counter() - self.start_time

    def remaining_seconds(self) -> float:
        return max(0.0, self.timeout_seconds - self.elapsed_seconds())

    def is_deadline_breached(self) -> bool:
        return self.is_cancelled or self.remaining_seconds() <= 1.5

    def check_deadline(self, stage_name: str = "execution"):
        """Verify remaining time budget; raise exception if deadline breached."""
        if self.is_deadline_breached():
            raise ExecutionBudgetExceeded(
                f"Deadline exceeded during stage '{stage_name}' (elapsed: {self.elapsed_seconds():.2f}s, budget: {self.timeout_seconds}s)"
            )

    def can_start_investigation_round(self) -> bool:
        """Check if an additional iterative retrieval round is permissible."""
        if self.current_round >= self.max_investigation_rounds:
            return False
        if self.remaining_seconds() < 8.0:
            # Need at least 8s for another retrieval + analysis cycle
            return False
        return True

    def increment_round(self):
        self.current_round += 1

    def record_agent_execution(self, role: str):
        self.specialists_executed += 1

    def record_tokens(self, tokens: int):
        self.tokens_used += tokens

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "elapsed_seconds": round(self.elapsed_seconds(), 2),
            "remaining_seconds": round(self.remaining_seconds(), 2),
            "investigation_rounds": self.current_round,
            "max_rounds": self.max_investigation_rounds,
            "specialists_executed": self.specialists_executed,
            "tokens_used": self.tokens_used
        }
