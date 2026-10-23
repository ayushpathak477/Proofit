import yfinance as yf
import pandas as pd
import time

def audit_indian_tickers():
    # Mix of Banks, IT, Manufacturing, and Pharma
    tickers = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "BAJFINANCE.NS", 
        "TATAMOTORS.NS", "SUNPHARMA.NS", "ITC.NS", "LT.NS", 
        "INFY.NS", "SBIN.NS"
    ]
    
    results = []
    
    for symbol in tickers:
        print(f"Auditing {symbol}...")
        ticker = yf.Ticker(symbol)
        
        # Check basic info and statements
        info = ticker.info
        income_stmt = ticker.financials
        balance_sheet = ticker.balance_sheet
        
        audit_record = {
            "Ticker": symbol,
            "Sector": info.get("sector", "Missing"),
            "Has_Income_Stmt": not income_stmt.empty,
            "Has_Balance_Sheet": not balance_sheet.empty,
            "Years_of_Data": len(income_stmt.columns) if not income_stmt.empty else 0,
            "Has_Total_Debt": "Total Debt" in balance_sheet.index if not balance_sheet.empty else False,
            "Has_Operating_Revenue": "Operating Revenue" in income_stmt.index if not income_stmt.empty else False
        }
        
        results.append(audit_record)
        time.sleep(1) # Be polite to the API
        
    df = pd.DataFrame(results)
    print("\n--- Audit Results ---")
    print(df.to_string())
    df.to_csv("storage/ticker_audit_results.csv", index=False)

if __name__ == "__main__":
    audit_indian_tickers()