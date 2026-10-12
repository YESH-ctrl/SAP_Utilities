"""
Deterministic Evidence Ledger and Provenance Aggregator for Agentic Platform.
Maintains request-scoped claim-to-evidence mappings, prevents multi-agent citation inflation,
tracks documented contradictions, and evaluates subquestion coverage matrices.
Operates strictly outside LLM generation as deterministic Python code.
"""

import logging
from typing import List, Dict, Set, Any, Optional
from sap_rag.agentic.schemas.contracts import (
    EvidenceItem,
    ClaimRecord,
    AgentFinding,
    ClaimSupportStatus,
    SubQuestion,
    QueryPlan
)

logger = logging.getLogger("sap_rag.agentic.ledger")


class EvidenceLedger:
    """
    In-memory deterministic evidence ledger and aggregator for a single user query turn.
    """

    def __init__(self, query_plan: QueryPlan):
        self.query_plan = query_plan
        # Indexed evidence items by evidence_id and chunk_id
        self._evidence_by_id: Dict[str, EvidenceItem] = {}
        self._chunk_to_evidence_id: Dict[int, str] = {}
        # Claim storage
        self._claims: List[ClaimRecord] = []
        # Agent findings
        self._findings: List[AgentFinding] = []
        # Contradictions
        self._contradictions: List[str] = []
        # Multi-agent citation tracking: maps chunk_id to set of agent roles that referenced it
        self._chunk_reference_counts: Dict[int, Set[str]] = {}

    def register_evidence_items(self, items: List[EvidenceItem]):
        """
        Register newly retrieved evidence items into the ledger.
        Ensures stable chunk deduplication.
        """
        for itm in items:
            if itm.chunk_id in self._chunk_to_evidence_id:
                # Already registered under this stable chunk ID
                continue
            self._evidence_by_id[itm.evidence_id] = itm
            self._chunk_to_evidence_id[itm.chunk_id] = itm.evidence_id

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceItem]:
        return self._evidence_by_id.get(evidence_id)

    def get_all_evidence(self) -> List[EvidenceItem]:
        return list(self._evidence_by_id.values())

    @staticmethod
    def classify_claim_category(claim_text: str) -> str:
        """
        Classifies claim text into one of the structured procedural categories:
        operation_identification, preconditions, transaction_codes, ordered_steps,
        expected_results, verification_procedures, exceptions_and_limitations, general.
        """
        txt = claim_text.lower()
        if any(k in txt for k in ("precondition", "prerequisite", "customizing", "settings for is-u")):
            return "preconditions"
        elif any(k in txt for k in ("t-code", "transaction code", "ec53e", "ec58e", "crm_ui", "navigation path", " -> ")):
            return "transaction_codes"
        elif any(k in txt for k in ("verify", "verification", "check the result", "webclient", "searchisu-contract", "search isu-contract")):
            return "verification_procedures"
        elif any(k in txt for k in ("exception", "limitation", "restriction", "billing has occurred", "subsequent billing", "cannot be reversed")):
            return "exceptions_and_limitations"
        elif any(k in txt for k in ("step 1", "step 2", "step 3", "open transaction", "press enter", "select the move-in", "select the move-out", "ordered step")):
            return "ordered_steps"
        elif any(k in txt for k in ("expected result", "outcome", "is reversed and", "is canceled", "overview displays", "no longer displays")):
            return "expected_results"
        elif any(k in txt for k in ("operation", "reversal of new", "reversal of end", "reconnection of a disconnected", "cancel contract change")):
            return "operation_identification"
        return "general"

    def audit_claim_validity(self, claim: ClaimRecord) -> ClaimRecord:
        """
        Audits an individual claim for:
        1. Improperly equating commercial contract reversal with physical service reconnection.
        2. Asserting transaction codes ungrounded in retrieved evidence.
        """
        txt = claim.claim_text.lower()
        
        # Rule 1: Service state vs Contract state separation
        # Reversing a contract (commercial/billing state) does NOT physically reconnect an installation/service
        equates_contract_and_service = (
            any(k in txt for k in ("reverse contract", "reversing a contract", "reversal of contract", "ec53e", "ec58e")) and
            any(k in txt for k in ("reconnects the installation", "reconnects physical service", "reconnects the utility", "restores service", "reconnects the meter", "automatically reconnects"))
        )

        qualification = claim.qualification
        status = claim.support_status
        is_equated = False

        if equates_contract_and_service:
            # Check if any retrieved evidence explicitly proves this equivalence
            has_corroborating_link = any(
                "reconnect" in e.content.lower() and "ec53e" in e.content.lower()
                for e in self._evidence_by_id.values()
            )
            if not has_corroborating_link:
                is_equated = True
                status = ClaimSupportStatus.CONTRADICTED
                qualification = (
                    "Rejected claim: In SAP Utilities, contract reversal (EC53E/EC58E) reverses move-in/move-out "
                    "billing documents but does not physically reconnect a disconnected utility installation. "
                    "Installation reconnection requires a Reconnection Order and Reconnection Entry under Disconnection/Reconnection processing."
                )

        # Rule 2: Unverified transaction codes
        # If claim asserts a specific T-code like EC50, VA01, etc. not in retrieved evidence
        import re
        tcode_matches = re.findall(r"\b([A-Z]{2,4}\d{2,4}[A-Z]?)\b", claim.claim_text)
        for tc in tcode_matches:
            if tc in ("CRM_UI", "ISU", "SAP"):
                continue
            tc_in_evidence = any(tc in e.content for e in self._evidence_by_id.values())
            if not tc_in_evidence and status == ClaimSupportStatus.SUPPORTED:
                status = ClaimSupportStatus.INSUFFICIENT_EVIDENCE
                qualification = f"Transaction code '{tc}' is ungrounded: Not found in retrieved evidence passages."

        cat = claim.claim_category or self.classify_claim_category(claim.claim_text)

        return claim.model_copy(update={
            "claim_category": cat,
            "support_status": status,
            "qualification": qualification,
            "is_service_state_equated": is_equated
        })

    def record_agent_finding(self, finding: AgentFinding):
        """
        Record a structured finding from a specialist agent.
        Audits claims, tracks multi-agent citations without artificial score inflation,
        and records reported contradictions.
        """
        self._findings.append(finding)

        # Track claims
        for claim in finding.atomic_claims:
            # Verify claimed supporting evidence IDs exist
            valid_supporting = [eid for eid in claim.supporting_evidence_ids if eid in self._evidence_by_id]
            valid_conflicting = [eid for eid in claim.contradictory_evidence_ids if eid in self._evidence_by_id]

            # Register multi-agent references per chunk
            for eid in valid_supporting:
                ev = self._evidence_by_id[eid]
                if ev.chunk_id not in self._chunk_reference_counts:
                    self._chunk_reference_counts[ev.chunk_id] = set()
                self._chunk_reference_counts[ev.chunk_id].add(finding.role)

            init_status = (
                ClaimSupportStatus.SUPPORTED if valid_supporting and not valid_conflicting else
                ClaimSupportStatus.CONTRADICTED if valid_conflicting and not valid_supporting else
                ClaimSupportStatus.PARTIALLY_SUPPORTED if valid_supporting and valid_conflicting else
                ClaimSupportStatus.INSUFFICIENT_EVIDENCE
            )

            audited_claim = claim.model_copy(update={
                "supporting_evidence_ids": valid_supporting,
                "contradictory_evidence_ids": valid_conflicting,
                "support_status": init_status
            })

            # Deep semantic audit for service state and T-code validity
            final_claim = self.audit_claim_validity(audited_claim)
            self._claims.append(final_claim)

        # Track reported conflicts
        if finding.conflicting_evidence_ids:
            conf_desc = (
                f"Role '{finding.role}' reported conflicting documentation across evidence "
                f"IDs: {finding.conflicting_evidence_ids}"
            )
            self._contradictions.append(conf_desc)

    def evaluate_coverage(self) -> Dict[str, Any]:
        """
        Evaluate coverage against the query plan's subquestions.
        Returns:
            - answered_subquestion_ids: List[str]
            - unresolved_subquestion_ids: List[str]
            - coverage_ratio: float
            - contradictions: List[str]
        """
        total_subqs = self.query_plan.subquestions
        if not total_subqs:
            # Single question query
            has_evidence = len(self._evidence_by_id) > 0
            return {
                "answered_subquestion_ids": ["Q-MAIN"] if has_evidence else [],
                "unresolved_subquestion_ids": [] if has_evidence else ["Q-MAIN"],
                "coverage_ratio": 1.0 if has_evidence else 0.0,
                "contradictions": self._contradictions,
                "claims_count": len(self._claims)
            }

        answered: Set[str] = set()
        unresolved: Set[str] = set()

        for sq in total_subqs:
            # A subquestion is answered if there is at least one finding or evidence item with similarity >= 0.55
            sq_findings = [f for f in self._findings if f.subquestion_id == sq.id and f.execution_status == "completed"]
            sq_evidence = [e for e in self._evidence_by_id.values() if e.subquery_id == sq.id and e.similarity_score >= 0.55]

            if (sq_findings and any(f.supporting_evidence_ids for f in sq_findings)) or len(sq_evidence) >= 1:
                answered.add(sq.id)
            else:
                unresolved.add(sq.id)

        coverage_ratio = len(answered) / len(total_subqs) if total_subqs else 1.0

        return {
            "answered_subquestion_ids": list(answered),
            "unresolved_subquestion_ids": list(unresolved),
            "coverage_ratio": round(coverage_ratio, 2),
            "contradictions": self._contradictions,
            "claims_count": len(self._claims)
        }

    def get_independent_corroboration_count(self, evidence_id: str) -> int:
        """
        Returns number of distinct agent roles that cited this evidence.
        Crucial: Does NOT treat multiple citations of the SAME chunk as multiple evidence items.
        """
        ev = self._evidence_by_id.get(evidence_id)
        if not ev:
            return 0
        return len(self._chunk_reference_counts.get(ev.chunk_id, set()))
