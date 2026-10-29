# graph/workflow.py
from langgraph.graph import StateGraph, START, END
from graph.state import ResearchState
from graph.routing import (
    route_after_validation, 
    route_valuation_by_sector, 
    route_after_verification
)
from data.yfinance_provider import YFinanceProvider
from data.schema import EvidenceRecord, Claim
from analysis.financial_metrics import (
    calculate_margins, 
    calculate_returns_and_leverage, 
    calculate_sector_valuation
)
from verification.verifier import verify_all_claims

provider = YFinanceProvider()

# --- 1. Data & Validation Nodes ---
def resolve_company(state: ResearchState) -> dict:
    ticker = state.get("ticker") or state.get("company", "")
    if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
        ticker = f"{ticker.upper()}.NS"
    return {"ticker": ticker, "retry_count": state.get("retry_count", 0)}

def collect_data(state: ResearchState) -> dict:
    ticker = state["ticker"]
    profile = provider.get_company_profile(ticker)
    financials = provider.get_financials(ticker) if not profile.error else None
    return {"profile": profile, "financials": financials}

def validate_data(state: ResearchState) -> dict:
    profile = state.get("profile")
    financials = state.get("financials")
    warnings = []
    evidence = {}

    if not profile or profile.error:
        warnings.append(f"Profile error: {profile.error if profile else 'Unknown'}")
        return {"data_warnings": warnings, "evidence": evidence}

    if not financials or not financials.income_statement:
        warnings.append("Missing income statement data.")
        return {"data_warnings": warnings, "evidence": evidence}

    # Pick latest year and populate canonical Evidence store using deterministic math
    latest_year = sorted(financials.income_statement.keys())[-1]
    margins = calculate_margins(financials, latest_year)
    returns = calculate_returns_and_leverage(financials, latest_year)

    all_metrics = {**margins, **returns}
    for metric_name, val in all_metrics.items():
        if val is not None:
            ev_id = f"ev_{metric_name}_{latest_year}"
            evidence[ev_id] = EvidenceRecord(
                evidence_id=ev_id,
                source_type="calculated_metric",
                source_url=f"https://finance.yahoo.com/quote/{profile.ticker}",
                period=latest_year,
                metric=metric_name,
                value=val,
                unit="percent" if "margin" in metric_name or metric_name in ("roe", "roce") else "ratio"
            )
        else:
            warnings.append(f"Could not compute {metric_name} for {latest_year}.")

    return {
        "research_period": latest_year,
        "evidence": evidence,
        "data_warnings": warnings
    }

# --- 2. Parallel Analytical Nodes (Stubs until Step 6) ---
def financial_analyst(state: ResearchState) -> dict:
    period = state.get("research_period", "Unknown")
    ev_id = f"ev_operating_margin_{period}"
    ev_store = state.get("evidence", {})
    
    if ev_id in ev_store:
        val = ev_store[ev_id].value
        claim = Claim(
            claim_id=f"fin_claim_1_{state.get('retry_count', 0)}",
            agent_name="financial_analyst",
            claim_type="numeric",
            statement=f"Operating margin was {val}% in {period}.",
            metric="operating_margin",
            value=val,
            unit="percent",
            period=period,
            evidence_ids=[ev_id]
        )
        return {"claims": [claim]}
    return {"claims": []}

def news_researcher(state: ResearchState) -> dict:
    return {"claims": []}

def industry_analyst(state: ResearchState) -> dict:
    return {"claims": []}

def risk_analyst(state: ResearchState) -> dict:
    return {"claims": []}

# --- 3. Valuation Nodes ---
def valuation_router(state: ResearchState) -> dict:
    """Synchronization join node after the 4 parallel agents finish."""
    return {}

def valuation_analyst(state: ResearchState) -> dict:
    val = calculate_sector_valuation(state["profile"], state["financials"], state["research_period"])
    return {"valuation_analysis": val}

def bank_nbfcs_valuation_analyst(state: ResearchState) -> dict:
    val = calculate_sector_valuation(state["profile"], state["financials"], state["research_period"])
    return {"valuation_analysis": val}

# --- 4. Debate, Verification & Retry Nodes ---
def bull_agent(state: ResearchState) -> dict:
    return {"bull_case": {"thesis": "Strong fundamentals backed by verified margins."}}

def bear_agent(state: ResearchState) -> dict:
    return {"bear_case": {"thesis": "Macro headwinds and valuation sensitivity."}}

def verify_claims(state: ResearchState) -> dict:
    claims = state.get("claims", [])
    evidence = state.get("evidence", {})
    results = verify_all_claims(claims, evidence)
    return {"verification_results": results}

def targeted_research_retry(state: ResearchState) -> dict:
    """Increments retry count and drops or repairs failed claims."""
    current_retries = state.get("retry_count", 0) + 1
    return {"retry_count": current_retries}

def generate_report(state: ResearchState) -> dict:
    profile = state.get("profile")
    if not profile or profile.error:
        return {"final_report": f"Research aborted: {profile.error if profile else 'Invalid company'}"}
    
    val_method = state.get("valuation_analysis", {}).get("methodology", "Unknown")
    verified_count = sum(1 for r in state.get("verification_results", {}).values() if r.status == "verified")
    
    report = (
        f"# Research Report: {profile.ticker}\n"
        f"- Sector: {profile.sector}\n"
        f"- Valuation Methodology: {val_method}\n"
        f"- Verified Claims: {verified_count}\n"
        f"- Warnings: {len(state.get('data_warnings', []))}"
    )
    return {"final_report": report}

# --- Build the Graph ---
def build_research_graph():
    builder = StateGraph(ResearchState)
    
    # Register all 15 nodes
    builder.add_node("resolve_company", resolve_company)
    builder.add_node("collect_data", collect_data)
    builder.add_node("validate_data", validate_data)
    builder.add_node("financial_analyst", financial_analyst)
    builder.add_node("news_researcher", news_researcher)
    builder.add_node("industry_analyst", industry_analyst)
    builder.add_node("risk_analyst", risk_analyst)
    builder.add_node("valuation_router", valuation_router)
    builder.add_node("valuation_analyst", valuation_analyst)
    builder.add_node("bank_nbfcs_valuation_analyst", bank_nbfcs_valuation_analyst)
    builder.add_node("bull_agent", bull_agent)
    builder.add_node("bear_agent", bear_agent)
    builder.add_node("verify_claims", verify_claims)
    builder.add_node("targeted_research_retry", targeted_research_retry)
    builder.add_node("generate_report", generate_report)

    # Wire sequential start
    builder.add_edge(START, "resolve_company")
    builder.add_edge("resolve_company", "collect_data")
    builder.add_edge("collect_data", "validate_data")

    # Conditional Fan-Out to parallel agents (or abort to report)
    builder.add_conditional_edges("validate_data", route_after_validation)

    # Fan-In: all 4 parallel agents converge on valuation_router
    builder.add_edge("financial_analyst", "valuation_router")
    builder.add_edge("news_researcher", "valuation_router")
    builder.add_edge("industry_analyst", "valuation_router")
    builder.add_edge("risk_analyst", "valuation_router")

    # Sector-aware conditional routing for valuation
    builder.add_conditional_edges("valuation_router", route_valuation_by_sector)

    # Both valuation paths converge on Bull -> Bear -> Verify
    builder.add_edge("valuation_analyst", "bull_agent")
    builder.add_edge("bank_nbfcs_valuation_analyst", "bull_agent")
    builder.add_edge("bull_agent", "bear_agent")
    builder.add_edge("bear_agent", "verify_claims")

    # Conditional verification loop (bounded retry)
    builder.add_conditional_edges("verify_claims", route_after_verification)
    builder.add_edge("targeted_research_retry", "verify_claims")

    builder.add_edge("generate_report", END)

    return builder.compile()