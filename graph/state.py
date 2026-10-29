# graph/state.py
import operator
from typing import TypedDict, Annotated, Dict, List, Optional, Any
from data.schema import (
    CompanyProfile, 
    FinancialStatements, 
    EvidenceRecord, 
    Claim, 
    VerificationOutcome
)

def merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Reducer to safely merge dictionaries from parallel nodes."""
    res = a.copy() if a else {}
    if b:
        res.update(b)
    return res

class ResearchState(TypedDict, total=False):
    company: str
    ticker: str
    research_period: str
    
    # Data Layer
    profile: Optional[CompanyProfile]
    financials: Optional[FinancialStatements]
    evidence: Annotated[Dict[str, EvidenceRecord], merge_dicts]
    data_warnings: Annotated[List[str], operator.add]
    
    # Agent Outputs (Annotated so parallel nodes append rather than overwrite)
    claims: Annotated[List[Claim], operator.add]
    valuation_analysis: Dict[str, Any]
    bull_case: Dict[str, Any]
    bear_case: Dict[str, Any]
    
    # Verification & Control Flow
    verification_results: Dict[str, VerificationOutcome]
    retry_count: int
    final_report: str