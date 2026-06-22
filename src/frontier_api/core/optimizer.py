import numpy as np
import scipy.optimize as sco
from typing import Dict, List, Tuple

TRADING_DAYS_PER_YEAR = 252

def portfolio_performance(weights: np.ndarray, mean_returns: np.ndarray, cov_matrix: np.ndarray) -> Tuple[float, float]:
    """Calculates annualized return and volatility for a given set of weights."""
    returns = np.sum(mean_returns * weights)
    std_dev = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    return returns, std_dev

def negative_sharpe_ratio(weights: np.ndarray, mean_returns: np.ndarray, cov_matrix: np.ndarray, risk_free_rate: float) -> float:
    """Objective function: Minimize the negative Sharpe Ratio to maximize the actual Sharpe Ratio."""
    p_ret, p_std = portfolio_performance(weights, mean_returns, cov_matrix)
    return - (p_ret - risk_free_rate) / p_std

def minimize_volatility(weights: np.ndarray, mean_returns: np.ndarray, cov_matrix: np.ndarray) -> float:
    """Objective function for the Efficient Frontier curve: Minimize volatility."""
    _, p_std = portfolio_performance(weights, mean_returns, cov_matrix)
    return p_std

def optimize_portfolio(returns_dict: Dict[str, List[float]], risk_free_rate: float = 0.04) -> dict:
    """
    The core engine. Takes periodic returns, calculates the Max Sharpe portfolio,
    and generates coordinates for the Efficient Frontier.
    """
    symbols = list(returns_dict.keys())
    
    # Convert dictionary to numpy array: shape (num_assets, num_observations)
    returns_matrix = np.array(list(returns_dict.values()))
    num_assets = len(symbols)

    # 1. Calculate Annualized Mean Returns and Covariance Matrix
    # np.cov expects rows to be variables (assets) and columns to be observations (days)
    mean_returns = np.mean(returns_matrix, axis=1) * TRADING_DAYS_PER_YEAR
    cov_matrix = np.cov(returns_matrix) * TRADING_DAYS_PER_YEAR

    # 2. Setup Optimization Constraints and Bounds
    # Constraint 1: All weights must sum exactly to 1.0 (100% of capital)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0})
    
    # Bounds: No short selling allowed in v1. Weights restricted between 0.0 and 1.0
    bounds = tuple((0.0, 1.0) for _ in range(num_assets))
    
    # Initial guess: Equal weighting across all assets
    initial_guess = np.array(num_assets * [1.0 / num_assets])

    # 3. Find Maximum Sharpe Ratio Portfolio
    opt_sharpe = sco.minimize(
        negative_sharpe_ratio,
        initial_guess,
        args=(mean_returns, cov_matrix, risk_free_rate),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    opt_weights = opt_sharpe.x
    opt_ret, opt_vol = portfolio_performance(opt_weights, mean_returns, cov_matrix)
    max_sharpe_ratio = (opt_ret - risk_free_rate) / opt_vol

    # Map weights back to their respective ticker symbols cleanly
    weights_dict = {symbols[i]: round(float(opt_weights[i]), 4) for i in range(num_assets)}

    # 4. Generate the Efficient Frontier Curve
    frontier_points = []
    
    # Define a range of target returns (from the worst asset's return to the best asset's return)
    min_ret = np.min(mean_returns)
    max_ret = np.max(mean_returns)
    target_returns = np.linspace(min_ret, max_ret, 20)

    for target in target_returns:
        # Constraint 2: The portfolio return must equal the specific target return for this point
        ef_constraints = (
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0},
            {'type': 'eq', 'fun': lambda x: portfolio_performance(x, mean_returns, cov_matrix)[0] - target}
        )
        
        ef_res = sco.minimize(
            minimize_volatility,
            initial_guess,
            args=(mean_returns, cov_matrix),
            method='SLSQP',
            bounds=bounds,
            constraints=ef_constraints
        )
        
        # Only append successful optimization points
        if ef_res.success:
            frontier_points.append({
                "volatility": round(float(ef_res.fun), 4),
                "return_rate": round(float(target), 4)
            })

    # 5. Format and Return the Result matching our Pydantic Schema
    return {
        "optimal_portfolio": {
            "sharpe_ratio": round(float(max_sharpe_ratio), 4),
            "expected_annual_return": round(float(opt_ret), 4),
            "annual_volatility": round(float(opt_vol), 4),
            "weights": weights_dict
        },
        "frontier_curve": frontier_points
    }