"""
frontier.api.main — FastAPI application entry-point.

Requires the [server] extra:

    pip install frontier-quant[server]
    uvicorn frontier.api.main:app --reload

The /v1/optimize_from_tickers endpoint additionally requires the [data] extra:

    pip install frontier-quant[data]

If that endpoint is called without [data] installed the server returns HTTP 501
with a clear installation instruction instead of crashing at startup.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from frontier import __version__

# Import Data Contracts (Phase 1)
from frontier.models.schemas import OptimizeRequest, TickerOptimizeRequest, OptimizeResponse

# Import Pure Math Engine (Phase 2)
from frontier.core.optimizer import optimize_portfolio

# NOTE: fetch_historical_returns is NOT imported here at module level.
# It is imported lazily inside optimize_from_tickers() so that the server
# can start without the optional [data] extra installed.

app = FastAPI(
    title="Frontier API",
    description="Stateless, high-performance Mean-Variance portfolio optimization engine.",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Standard CORS setup to ensure web dashboards can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace "*" with your frontend's actual URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/v1/optimize", response_model=OptimizeResponse)
async def optimize_pure_math(request: OptimizeRequest):
    """
    Endpoint 1: The Pure Quantitative Engine.

    Accepts pre-calculated arrays of asset returns.
    Does not rely on external internet calls.
    Ideal for institutional users with proprietary data feeds.

    Requires only the core install::

        pip install frontier-quant
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

    Takes stock tickers, fetches historical adjusted closing prices via
    Yahoo Finance, calculates periodic returns, and passes them to the math
    engine.

    Requires the [data] extra in addition to [server]::

        pip install frontier-quant[data]

    If [data] is not installed the endpoint returns HTTP 501 with installation
    instructions instead of crashing the server.
    """
    # ---------------------------------------------------------------------------
    # Lazy import — the data adapter is optional.  Importing it here (inside the
    # handler, not at module level) means the server starts cleanly with only the
    # [server] extra installed.  The 501 response guides users toward the fix.
    # ---------------------------------------------------------------------------
    try:
        from frontier.adapters.yfinance_client import fetch_historical_returns
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail=(
                "The /v1/optimize_from_tickers endpoint requires the optional "
                "'data' dependencies.\n\n"
                "Install them with:\n\n"
                "    pip install frontier-quant[data]"
            ),
        )

    try:
        # Step 1: Pass tickers to the adapter to get clean return data
        returns_dict = fetch_historical_returns(request.tickers, request.lookback_years)

        # Step 2: Pass the clean data into the math engine
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