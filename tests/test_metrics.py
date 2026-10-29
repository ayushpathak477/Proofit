# tests/test_metrics.py
from data.schema import CompanyProfile, FinancialStatements
from analysis.financial_metrics import (
    calculate_margins, 
    calculate_returns_and_leverage, 
    calculate_sector_valuation
)

def test_margin_calculations():
    dummy_data = FinancialStatements(
        ticker="TEST",
        income_statement={
            "2025": {
                "Total Revenue": 1000.0,
                "Operating Income": 150.0,
                "Net Income": 100.0
            }
        }
    )
    margins = calculate_margins(dummy_data, "2025")
    assert margins["operating_margin"] == 15.0
    assert margins["net_margin"] == 10.0

def test_returns_and_leverage():
    dummy_data = FinancialStatements(
        ticker="TEST",
        income_statement={"2025": {"Net Income": 200.0, "Operating Income": 300.0}},
        balance_sheet={
            "2025": {
                "Total Debt": 500.0,
                "Stockholders Equity": 1000.0,
                "Total Assets": 2000.0,
                "Current Liabilities": 500.0
            }
        },
        cash_flow={"2025": {"Operating Cash Flow": 400.0, "Capital Expenditure": -100.0}}
    )
    metrics = calculate_returns_and_leverage(dummy_data, "2025")
    assert metrics["roe"] == 20.0
    assert metrics["roce"] == 20.0
    assert metrics["debt_to_equity"] == 0.5
    assert metrics["free_cash_flow"] == 300.0

def test_bank_valuation_routing():
    bank_profile = CompanyProfile(ticker="HDFCBANK.NS", sector="Financial Services", market_cap=10000.0)
    bank_fin = FinancialStatements(
        ticker="HDFCBANK.NS",
        income_statement={"2025": {"Net Income": 1000.0}},
        balance_sheet={"2025": {"Stockholders Equity": 5000.0}}
    )
    val = calculate_sector_valuation(bank_profile, bank_fin, "2025")
    assert val["methodology"] == "Bank_NBFC_PB_ROE_Model"
    assert val["dcf_applicable"] is False
    assert val["pe_ratio"] == 10.0
    assert val["pb_ratio"] == 2.0