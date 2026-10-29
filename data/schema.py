from pydantic import BaseModel
from typing import Optional, Dict


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
