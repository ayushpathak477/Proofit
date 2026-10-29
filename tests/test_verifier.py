# tests/test_verifier.py
from data.schema import Claim, EvidenceRecord
from verification.verifier import verify_single_claim

def get_sample_evidence():
    return {
        "ev_op_margin_2025": EvidenceRecord(
            evidence_id="ev_op_margin_2025",
            source_type="calculated_metric",
            source_url="https://finance.yahoo.com/quote/TCS.NS",
            period="2025",
            metric="operating_margin",
            value=24.5,
            unit="percent"
        )
    }

def test_valid_numeric_claim():
    evidence = get_sample_evidence()
    claim = Claim(
        claim_id="c1",
        agent_name="financial_analyst",
        claim_type="numeric",
        statement="Operating margin stood at 24.5% in 2025.",
        metric="operating_margin",
        value=24.5,
        unit="percent",
        period="2025",
        evidence_ids=["ev_op_margin_2025"]
    )
    res = verify_single_claim(claim, evidence)
    assert res.status == "verified"

def test_hallucinated_number_fails():
    evidence = get_sample_evidence()
    # Agent hallucinates 30.0% instead of 24.5%
    claim = Claim(
        claim_id="c2",
        agent_name="financial_analyst",
        claim_type="numeric",
        statement="Operating margin surged to 30.0% in 2025.",
        metric="operating_margin",
        value=30.0,
        unit="percent",
        period="2025",
        evidence_ids=["ev_op_margin_2025"]
    )
    res = verify_single_claim(claim, evidence)
    assert res.status == "failed"
    assert "Numeric mismatch" in res.reason

def test_period_mismatch_fails():
    evidence = get_sample_evidence()
    # Agent cites 2025 evidence for a 2026 claim
    claim = Claim(
        claim_id="c3",
        agent_name="financial_analyst",
        claim_type="numeric",
        statement="Operating margin was 24.5% in 2026.",
        metric="operating_margin",
        value=24.5,
        unit="percent",
        period="2026",
        evidence_ids=["ev_op_margin_2025"]
    )
    res = verify_single_claim(claim, evidence)
    assert res.status == "failed"
    assert "Period mismatch" in res.reason