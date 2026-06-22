from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import Data Contracts (Phase 1)
from frontier_api.models.schemas import OptimizeRequest, TickerOptimizeRequest, OptimizeResponse

# Import Pure Math Engine (Phase 2)
from frontier_api.core.optimizer import optimize_portfolio

# Import Market Data Adapter (Phase 3)
from frontier_api.adapters.yfinance_client import fetch_historical_returns

app = FastAPI(
    title="Frontier API",
    description="Stateless, high-performance Mean-Variance portfolio optimization engine.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Standard CORS setup to ensure web dashboards can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace "*" with your frontend's actual URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/v1/optimize", response_model=OptimizeResponse)
async def optimize_pure_math(request: OptimizeRequest):
    """
    Endpoint 1: The Pure Quantitative Engine.
    Accepts pre-calculated arrays of asset returns. Does not rely on external internet calls.
    Ideal for institutional users with proprietary data feeds.
    """
    try:
        result = optimize_portfolio(request.returns, request.risk_free_rate)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Optimization failed: {str(e)}")

@app.post("/v1/optimize_from_tickers", response_model=OptimizeResponse)
async def optimize_from_tickers(request: TickerOptimizeRequest):
    """
    Endpoint 2: The Convenience Engine.
    Takes stock tickers, fetches historical adjusted closing prices via yfinance, 
    calculates periodic returns, and passes them to the math engine.
    """
    try:
        # Step 1: Pass tickers to the Phase 3 adapter to get clean data
        returns_dict = fetch_historical_returns(request.tickers, request.lookback_years)
        
        # Step 2: Pass the clean data into the Phase 2 math engine
        result = optimize_portfolio(returns_dict, request.risk_free_rate)
        
        return result
    except ValueError as ve:
        # Catches specifically handled data errors (like invalid tickers or zero data rows)
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        # Catches Yahoo Finance connection failures
        raise HTTPException(status_code=502, detail=str(re))
    except Exception as e:
        # Fallback for unexpected math/server errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/health")
async def health_check():
    """Simple health ping to ensure the server is active."""
    return {"status": "active", "service": "Frontier API"}