# data/schema.py
from pydantic import BaseModel
from typing import Optional, Dict, List, Literal

class CompanyProfile(BaseModel):
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    current_price: Optional[float] = None
    error: Optional[str] = None

class FinancialStatements(BaseModel):
    ticker: str
    income_statement: Dict[str, Dict[str, float]] = {}
    balance_sheet: Dict[str, Dict[str, float]] = {}
    cash_flow: Dict[str, Dict[str, float]] = {}
    error: Optional[str] = None

class EvidenceRecord(BaseModel):
    evidence_id: str
    source_type: Literal["financial_statement", "calculated_metric", "news", "filing"]
    source_url: str
    period: str
    metric: str
    value: Optional[float] = None
    unit: str = "number"
    text_snippet: Optional[str] = None

class Claim(BaseModel):
    claim_id: str
    agent_name: str
    claim_type: Literal["numeric", "qualitative"]
    statement: str
    metric: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    period: Optional[str] = None
    evidence_ids: List[str]

class VerificationOutcome(BaseModel):
    claim_id: str
    status: Literal["verified", "failed", "insufficient_evidence"]
    reason: str