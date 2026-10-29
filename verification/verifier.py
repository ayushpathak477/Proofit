# verification/verifier.py
from typing import Dict, List
from data.schema import Claim, EvidenceRecord, VerificationOutcome

def verify_single_claim(
    claim: Claim, 
    evidence_store: Dict[str, EvidenceRecord], 
    tolerance: float = 0.1
) -> VerificationOutcome:
    """
    Deterministically verifies an agent's claim against canonical evidence records.
    """
    # Rule 1: Every material claim must cite at least one evidence ID
    if not claim.evidence_ids:
        return VerificationOutcome(
            claim_id=claim.claim_id,
            status="insufficient_evidence",
            reason="No evidence IDs cited for this claim."
        )

    # Rule 2: All cited evidence IDs must actually exist in our evidence store
    missing_ids = [eid for eid in claim.evidence_ids if eid not in evidence_store]
    if missing_ids:
        return VerificationOutcome(
            claim_id=claim.claim_id,
            status="failed",
            reason=f"Hallucinated or missing evidence IDs: {missing_ids}"
        )

    # Rule 3: For numeric claims, check period and value against primary evidence
    if claim.claim_type == "numeric":
        if claim.value is None:
            return VerificationOutcome(
                claim_id=claim.claim_id,
                status="failed",
                reason="Numeric claim is missing a numeric 'value' field."
            )

        primary_ev = evidence_store[claim.evidence_ids[0]]

        # Check period match (e.g., prevent citing FY2024 data as FY2025)
        if claim.period and primary_ev.period and claim.period != primary_ev.period:
            return VerificationOutcome(
                claim_id=claim.claim_id,
                status="failed",
                reason=f"Period mismatch: Claim states {claim.period}, but evidence is for {primary_ev.period}."
            )

        if primary_ev.value is None:
            return VerificationOutcome(
                claim_id=claim.claim_id,
                status="insufficient_evidence",
                reason=f"Evidence '{primary_ev.evidence_id}' does not contain a numeric value."
            )

        # Check arithmetic match within rounding tolerance
        diff = abs(claim.value - primary_ev.value)
        if diff > tolerance:
            return VerificationOutcome(
                claim_id=claim.claim_id,
                status="failed",
                reason=f"Numeric mismatch: Agent claimed {claim.value}, but canonical evidence is {primary_ev.value} (diff {diff:.2f} > tolerance {tolerance})."
            )

    return VerificationOutcome(
        claim_id=claim.claim_id,
        status="verified",
        reason="Claim verified against canonical evidence."
    )

def verify_all_claims(
    claims: List[Claim], 
    evidence_store: Dict[str, EvidenceRecord]
) -> Dict[str, VerificationOutcome]:
    """Runs verification across a batch of claims."""
    return {c.claim_id: verify_single_claim(c, evidence_store) for c in claims}