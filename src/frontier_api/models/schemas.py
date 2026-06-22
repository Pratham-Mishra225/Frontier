from pydantic import BaseModel, Field
from typing import Dict, List

# ==========================================
# REQUEST MODELS (Input Data)
# ==========================================

class OptimizeRequest(BaseModel):
    """
    Payload for Endpoint 1 (Pure Math).
    Expects pre-calculated periodic returns for each asset.
    """
    returns: Dict[str, List[float]] = Field(
        ...,
        description="Dictionary where keys are asset symbols and values are arrays of historical returns."
    )
    risk_free_rate: float = Field(
        default=0.04,
        description="Annualized risk-free rate used for the Sharpe Ratio calculation (Default: 4%)."
    )

class TickerOptimizeRequest(BaseModel):
    """
    Payload for Endpoint 2 (Convenience/Adapter).
    Expects a list of ticker symbols to be fetched via yfinance.
    """
    tickers: List[str] = Field(
        ...,
        min_length=2,
        description="List of stock tickers to optimize (e.g., ['AAPL', 'MSFT', 'GOOG'])."
    )
    lookback_years: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Number of years of historical data to fetch (Default: 3)."
    )
    risk_free_rate: float = Field(
        default=0.04,
        description="Annualized risk-free rate used for the Sharpe Ratio calculation (Default: 4%)."
    )

# ==========================================
# RESPONSE MODELS (Output Data)
# ==========================================

class PortfolioMetrics(BaseModel):
    """
    The exact mathematical properties of the optimized portfolio.
    """
    sharpe_ratio: float
    expected_annual_return: float
    annual_volatility: float
    weights: Dict[str, float] = Field(
        ...,
        description="The exact allocation percentages summing to 1.0"
    )

class FrontierPoint(BaseModel):
    """
    A single X,Y coordinate for plotting the Efficient Frontier curve.
    """
    volatility: float
    return_rate: float  # Using 'return_rate' because 'return' is a Python keyword

class OptimizeResponse(BaseModel):
    """
    The final, standardized JSON payload returned to the client.
    """
    status: str = "success"
    metadata: dict = Field(default={}, description="Information about the data source and timeframe")
    optimal_portfolio: PortfolioMetrics
    frontier_curve: List[FrontierPoint]