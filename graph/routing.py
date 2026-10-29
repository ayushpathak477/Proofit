# graph/routing.py
from typing import List, Union
from graph.state import ResearchState

def route_after_validation(state: ResearchState) -> Union[List[str], str]:
    """
    If critical data is missing (e.g., invalid ticker), skip straight to report generation.
    Otherwise, fan out to the 4 analytical agents in parallel.
    """
    profile = state.get("profile")
    if not profile or profile.error:
        return "generate_report"
    
    # Fan-out: LangGraph executes all returned nodes in parallel
    return [
        "financial_analyst", 
        "news_researcher", 
        "industry_analyst", 
        "risk_analyst"
    ]

def route_valuation_by_sector(state: ResearchState) -> str:
    """Routes Banks/NBFCs to P/B & ROE model, and others to DCF/Multiples."""
    profile = state.get("profile")
    if profile and profile.sector == "Financial Services":
        return "bank_nbfcs_valuation_analyst"
    return "valuation_analyst"

def route_after_verification(state: ResearchState) -> str:
    """
    Checks if any claim failed verification. 
    If failures exist and retry_count < 2, loop back for targeted retry.
    """
    results = state.get("verification_results", {})
    retry_count = state.get("retry_count", 0)
    
    has_failures = any(outcome.status == "failed" for outcome in results.values())
    
    if has_failures and retry_count < 2:
        return "targeted_research_retry"
    return "generate_report"