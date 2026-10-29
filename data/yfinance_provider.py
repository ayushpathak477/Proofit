import yfinance as yf
from data.provider_interface import MarketDataProvider
from data.schema import CompanyProfile, FinancialStatements

class YFinanceProvider(MarketDataProvider):
    def get_company_profile(self, ticker: str) -> CompanyProfile:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # If the ticker is dead (like TATAMOTORS.NS), info will be mostly empty or throw an error
            if not info or "symbol" not in info:
                return CompanyProfile(ticker=ticker, error="Ticker not found or delisted.")
                
            return CompanyProfile(
                ticker=ticker,
                sector=info.get("sector"),
                industry=info.get("industry"),
                market_cap=info.get("marketCap"),
                current_price=info.get("currentPrice")
            )
        except Exception as e:
            return CompanyProfile(ticker=ticker, error=str(e))

    def get_financials(self, ticker: str) -> FinancialStatements:
        try:
            stock = yf.Ticker(ticker)
            # Convert DataFrames to dicts, replacing NaN with 0.0 to avoid breaking JSON/math later
            inc = stock.financials.fillna(0).to_dict() if not stock.financials.empty else {}
            bal = stock.balance_sheet.fillna(0).to_dict() if not stock.balance_sheet.empty else {}
            cf = stock.cashflow.fillna(0).to_dict() if not stock.cashflow.empty else {}
            
            if not inc and not bal and not cf:
                 return FinancialStatements(ticker=ticker, income_statement={}, balance_sheet={}, cash_flow={}, error="No financial data found.")

            # Convert timestamps to string years for cleaner JSON
            clean_inc = {str(k)[:10]: v for k, v in inc.items()}
            clean_bal = {str(k)[:10]: v for k, v in bal.items()}
            clean_cf = {str(k)[:10]: v for k, v in cf.items()}

            return FinancialStatements(
                ticker=ticker,
                income_statement=clean_inc,
                balance_sheet=clean_bal,
                cash_flow=clean_cf
            )
        except Exception as e:
            return FinancialStatements(ticker=ticker, income_statement={}, balance_sheet={}, cash_flow={}, error=str(e))