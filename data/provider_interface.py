from abc import ABC, abstractmethod
from data.schema import CompanyProfile, FinancialStatements


class MarketDataProvider(ABC):
    @abstractmethod
    def get_company_profile(self, ticker: str) -> CompanyProfile:
        pass

    @abstractmethod
    def get_financials(self, ticker: str) -> FinancialStatements:
        pass
