"""
Statistical Analysis & Monte Carlo Risk Engine:
Hurst Exponent, Return Autocorrelations, Anomaly Detection, and 1000-Path Monte Carlo Simulation
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd

class StatisticalAnalyzer:
    @staticmethod
    def calculate_hurst_exponent(price_series: np.ndarray, max_lags: int = 20) -> float:
        """
        Calculate Hurst Exponent (H) via Rescaled Range (R/S) analysis.
        H > 0.55: Persistent / Trending
        H < 0.45: Anti-persistent / Mean-Reverting
        H ~ 0.50: Random Walk
        """
        if len(price_series) < 50:
            return 0.50

        lags = range(2, min(max_lags, len(price_series) // 4))
        tau = []
        for lag in lags:
            # Price differences at given lag
            diffs = price_series[lag:] - price_series[:-lag]
            tau.append(np.std(diffs))

        if len(tau) < 3 or any(t <= 0 for t in tau):
            return 0.50

        # Linear regression on log(tau) vs log(lag)
        poly = np.polyfit(np.log(list(lags)), np.log(tau), 1)
        hurst = float(poly[0])
        return max(0.05, min(0.95, hurst))

    @classmethod
    def detect_anomalies(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect statistical anomalies in price, volume, and volatility."""
        if df.empty or len(df) < 30:
            return {"anomaly_detected": False, "anomaly_score": 0.0, "anomaly_type": "NONE"}

        returns = df["close"].pct_change().dropna()
        vols = df["volume"].dropna()

        # Z-scores of last bar
        ret_z = (returns.iloc[-1] - returns.mean()) / (returns.std() + 1e-9)
        vol_z = (vols.iloc[-1] - vols.mean()) / (vols.std() + 1e-9)

        anomaly_score = float(min(100.0, (abs(ret_z) * 20.0 + max(0, vol_z) * 15.0)))
        is_anomaly = anomaly_score > 60.0

        anomaly_type = "NONE"
        if is_anomaly:
            if ret_z > 2.5 and vol_z > 2.0:
                anomaly_type = "ABNORMAL_BULLISH_VOLUME_SURGE"
            elif ret_z < -2.5 and vol_z > 2.0:
                anomaly_type = "ABNORMAL_PANIC_SELL_DUMP"
            elif vol_z > 3.5:
                anomaly_type = "EXTREME_VOLUME_OUTLIER"
            elif abs(ret_z) > 3.0:
                anomaly_type = "FLASH_VOLATILITY_SPIKE"

        return {
            "anomaly_detected": is_anomaly,
            "anomaly_score": round(anomaly_score, 1),
            "anomaly_type": anomaly_type,
            "return_z_score": round(float(ret_z), 2),
            "volume_z_score": round(float(vol_z), 2)
        }

    @classmethod
    def run_monte_carlo_simulation(
        cls,
        current_price: float,
        daily_volatility_pct: float,
        horizon_hours: int = 24,
        num_simulations: int = 1000
    ) -> Dict[str, Any]:
        """
        Run 1,000-path Geometric Brownian Motion Monte Carlo simulation with Jump Diffusion.
        Calculates projected price distribution, VaR (95%, 99%), and probability cones.
        """
        dt = 1.0 / 24.0 # hourly step
        sigma = (daily_volatility_pct / 100.0) / np.sqrt(365) * np.sqrt(24) # hourly sigma
        mu = 0.0001 # slight drift

        np.random.seed(42)
        # Brownian increments
        shocks = np.random.normal(
            (mu - 0.5 * sigma**2) * dt,
            sigma * np.sqrt(dt),
            size=(num_simulations, horizon_hours)
        )

        # Jump diffusion (Poisson jumps: 2% chance of 1.5% shock)
        jumps = np.random.choice([0.0, 0.015, -0.015], size=(num_simulations, horizon_hours), p=[0.96, 0.02, 0.02])
        shocks += jumps

        price_paths = np.zeros((num_simulations, horizon_hours + 1))
        price_paths[:, 0] = current_price

        for t in range(1, horizon_hours + 1):
            price_paths[:, t] = price_paths[:, t - 1] * np.exp(shocks[:, t - 1])

        # Statistical percentiles across simulation horizon
        final_prices = price_paths[:, -1]
        p5 = np.percentile(final_prices, 5)   # 95% VaR floor
        p1 = np.percentile(final_prices, 1)   # 99% VaR floor
        p25 = np.percentile(final_prices, 25)
        p50 = np.percentile(final_prices, 50) # Median path
        p75 = np.percentile(final_prices, 75)
        p95 = np.percentile(final_prices, 95) # 95% Ceiling

        # VaR (Value at Risk in USD and %)
        var_95_usd = current_price - p5
        var_95_pct = (var_95_usd / current_price) * 100
        var_99_usd = current_price - p1
        var_99_pct = (var_99_usd / current_price) * 100

        # Conditional VaR (Expected Shortfall beyond 95%)
        tail_losses = current_price - final_prices[final_prices <= p5]
        cvar_95_usd = np.mean(tail_losses) if len(tail_losses) > 0 else var_95_usd
        cvar_95_pct = (cvar_95_usd / current_price) * 100

        # Time series quantile paths for frontend chart
        quantile_steps = []
        for step in range(horizon_hours + 1):
            prices_at_t = price_paths[:, step]
            quantile_steps.append({
                "step_hour": step,
                "p5": round(float(np.percentile(prices_at_t, 5)), 2),
                "p25": round(float(np.percentile(prices_at_t, 25)), 2),
                "median": round(float(np.percentile(prices_at_t, 50)), 2),
                "p75": round(float(np.percentile(prices_at_t, 75)), 2),
                "p95": round(float(np.percentile(prices_at_t, 95)), 2),
            })

        prob_profit_long = float(np.mean(final_prices > current_price)) * 100
        prob_profit_short = 100.0 - prob_profit_long

        return {
            "current_price": round(current_price, 2),
            "simulations_count": num_simulations,
            "horizon_hours": horizon_hours,
            "median_projection": round(float(p50), 2),
            "p95_upper_target": round(float(p95), 2),
            "p5_lower_floor": round(float(p5), 2),
            "var_95_usd": round(float(var_95_usd), 2),
            "var_95_pct": round(float(var_95_pct), 2),
            "var_99_usd": round(float(var_99_usd), 2),
            "var_99_pct": round(float(var_99_pct), 2),
            "cvar_95_pct": round(float(cvar_95_pct), 2),
            "prob_higher_24h": round(prob_profit_long, 1),
            "prob_lower_24h": round(prob_profit_short, 1),
            "path_projection_series": quantile_steps
        }
