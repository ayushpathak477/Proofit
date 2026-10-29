# tests/test_graph.py
from data.schema import CompanyProfile, Claim, EvidenceRecord, VerificationOutcome
from graph.routing import (
    route_after_validation, 
    route_valuation_by_sector, 
    route_after_verification
)
from graph.workflow import build_research_graph

def test_route_after_validation_fans_out():
    state = {"profile": CompanyProfile(ticker="TCS.NS", sector="Technology")}
    next_nodes = route_after_validation(state)
    assert isinstance(next_nodes, list)
    assert len(next_nodes) == 4
    assert "financial_analyst" in next_nodes

def test_route_after_validation_aborts_on_error():
    state = {"profile": CompanyProfile(ticker="BAD.NS", error="Ticker not found")}
    assert route_after_validation(state) == "generate_report"

def test_sector_routing_for_banks_vs_it():
    bank_state = {"profile": CompanyProfile(ticker="HDFCBANK.NS", sector="Financial Services")}
    it_state = {"profile": CompanyProfile(ticker="TCS.NS", sector="Technology")}
    assert route_valuation_by_sector(bank_state) == "bank_nbfcs_valuation_analyst"
    assert route_valuation_by_sector(it_state) == "valuation_analyst"

def test_bounded_retry_routing():
    failed_outcome = VerificationOutcome(claim_id="c1", status="failed", reason="Bad math")
    
    # Retry 0 -> should trigger retry node
    state_retry_0 = {"verification_results": {"c1": failed_outcome}, "retry_count": 0}
    assert route_after_verification(state_retry_0) == "targeted_research_retry"
    
    # Retry 2 -> hits bound, must exit to generate_report
    state_retry_2 = {"verification_results": {"c1": failed_outcome}, "retry_count": 2}
    assert route_after_verification(state_retry_2) == "generate_report"

def test_end_to_end_graph_compiles_and_runs_live():
    graph = build_research_graph()
    result = graph.invoke({"company": "TCS"})
    assert result["ticker"] == "TCS.NS"
    assert result["valuation_analysis"]["methodology"] in ("DCF_and_Multiples", "Multiples_Only")
    assert "Research Report: TCS.NS" in result["final_report"]