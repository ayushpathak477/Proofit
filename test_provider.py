from data.yfinance_provider import YFinanceProvider

provider = YFinanceProvider()

# Test a working one
reliance = provider.get_company_profile("RELIANCE.NS")
print(reliance)

# Test our dead Tata Motors ticker to see it fail gracefully
tata = provider.get_company_profile("TATAMOTORS.NS")
print(tata)

# Test the new Tata Motors CV ticker
tata_cv = provider.get_company_profile("TMCV.NS")
print(tata_cv)