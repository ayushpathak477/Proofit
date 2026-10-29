# analysis/financial_metrics.py
from data.schema import CompanyProfile, FinancialStatements
from typing import Dict, Optional, Any

def calculate_growth(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    """Calculates percentage growth between two periods."""
    if current is not None and previous is not None and previous != 0:
        return round(((current - previous) / abs(previous)) * 100, 2)
    return None

def calculate_margins(financials: FinancialStatements, year: str) -> Dict[str, Optional[float]]:
    """Calculates Operating and Net Profit margins."""
    inc = financials.income_statement.get(year, {})
    revenue = inc.get("Total Revenue") or inc.get("Operating Revenue")
    operating_income = inc.get("Operating Income") or inc.get("EBIT")
    net_income = inc.get("Net Income")

    margins = {"operating_margin": None, "net_margin": None}
    if revenue and revenue > 0:
        if operating_income is not None:
            margins["operating_margin"] = round((operating_income / revenue) * 100, 2)
        if net_income is not None:
            margins["net_margin"] = round((net_income / revenue) * 100, 2)
    return margins

def calculate_returns_and_leverage(financials: FinancialStatements, year: str) -> Dict[str, Optional[float]]:
    """Calculates ROE, ROCE, Debt/Equity, and Free Cash Flow."""
    inc = financials.income_statement.get(year, {})
    bal = financials.balance_sheet.get(year, {})
    cf = financials.cash_flow.get(year, {})

    net_income = inc.get("Net Income")
    ebit = inc.get("Operating Income") or inc.get("EBIT")
    
    equity = bal.get("Stockholders Equity") or bal.get("Total Stockholder Equity")
    total_debt = bal.get("Total Debt")
    total_assets = bal.get("Total Assets")
    current_liabilities = bal.get("Current Liabilities")

    op_cash_flow = cf.get("Operating Cash Flow")
    capex = cf.get("Capital Expenditure")

    metrics = {
        "roe": None,
        "roce": None,
        "debt_to_equity": None,
        "free_cash_flow": None
    }

    # ROE = Net Income / Equity
    if net_income is not None and equity and equity > 0:
        metrics["roe"] = round((net_income / equity) * 100, 2)

    # ROCE = EBIT / (Total Assets - Current Liabilities)
    if ebit is not None and total_assets and current_liabilities is not None:
        capital_employed = total_assets - current_liabilities
        if capital_employed > 0:
            metrics["roce"] = round((ebit / capital_employed) * 100, 2)

    # Debt / Equity
    if total_debt is not None and equity and equity > 0:
        metrics["debt_to_equity"] = round(total_debt / equity, 2)

    # Free Cash Flow = Operating Cash Flow + CapEx (CapEx is usually negative in yfinance, so we handle both)
    if op_cash_flow is not None and capex is not None:
        fcf = op_cash_flow - abs(capex)
        metrics["free_cash_flow"] = round(fcf, 2)

    return metrics

def calculate_sector_valuation(
    profile: CompanyProfile, 
    financials: FinancialStatements, 
    latest_year: str
) -> Dict[str, Any]:
    """
    Routes valuation methodology by sector:
    - Financial Services (Banks/NBFCs): Uses P/B, P/E, and ROE-based excess return model.
    - Non-Financials: Uses P/E and 3-scenario (Bear/Base/Bull) FCF valuation.
    """
    inc = financials.income_statement.get(latest_year, {})
    bal = financials.balance_sheet.get(latest_year, {})
    
    net_income = inc.get("Net Income")
    equity = bal.get("Stockholders Equity") or bal.get("Total Stockholder Equity")
    mcap = profile.market_cap

    pe_ratio = round(mcap / net_income, 2) if (mcap and net_income and net_income > 0) else None
    pb_ratio = round(mcap / equity, 2) if (mcap and equity and equity > 0) else None

    is_financial = profile.sector == "Financial Services"

    if is_financial:
        return {
            "methodology": "Bank_NBFC_PB_ROE_Model",
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "dcf_applicable": False,
            "reason": "Conventional FCF DCF is not applicable to Banks/NBFCs; evaluated using P/B and ROE."
        }
    
    # Non-financials: check if we can run a simple 5-year FCF scenario model
    ret_metrics = calculate_returns_and_leverage(financials, latest_year)
    fcf = ret_metrics["free_cash_flow"]

    if not fcf or fcf <= 0:
        return {
            "methodology": "Multiples_Only",
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "dcf_applicable": False,
            "reason": "Free Cash Flow is negative or unavailable; skipping DCF scenario analysis."
        }

    # Simple 5-year DCF scenarios (Bear: 5% growth, Base: 10% growth, Bull: 15% growth; 12% discount rate, 4% terminal)
    scenarios = {}
    for case, g in [("bear_case", 0.05), ("base_case", 0.10), ("bull_case", 0.15)]:
        discount_rate = 0.12
        terminal_growth = 0.04
        pv_fcf = sum([fcf * ((1 + g) ** t) / ((1 + discount_rate) ** t) for t in range(1, 6)])
        terminal_fcf = fcf * ((1 + g) ** 5) * (1 + terminal_growth)
        terminal_value = terminal_fcf / (discount_rate - terminal_growth)
        pv_terminal = terminal_value / ((1 + discount_rate) ** 5)
        scenarios[case] = round(pv_fcf + pv_terminal, 2)

    return {
        "methodology": "DCF_and_Multiples",
        "pe_ratio": pe_ratio,
        "pb_ratio": pb_ratio,
        "dcf_applicable": True,
        "assumptions": {
            "discount_rate": 0.12,
            "terminal_growth": 0.04,
            "growth_rates": {"bear_case": 0.05, "base_case": 0.10, "bull_case": 0.15}
        },
        "intrinsic_value_scenarios": scenarios
    }