"""
AI Recommendation Engine — generates buy/wait advice based on ML predictions.
"""
import numpy as np
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Recommendation:
    recommendation: str       # BUY_NOW | WAIT | PRICE_LIKELY_DECREASE | PRICE_LIKELY_INCREASE
    confidence: float         # 0.0 – 1.0
    reason: str
    best_time_to_buy: Optional[str]
    expected_price: Optional[float]


def generate_recommendation(
    current_price: float,
    predictions: List[dict],
    prices_history: List[float],
    lowest_ever: Optional[float] = None,
    target_price: Optional[float] = None,
) -> Recommendation:
    """
    Analyze predicted prices and history to generate a buy recommendation.

    Logic:
    - If predicted next 7 days avg < current → WAIT (price likely to drop)
    - If current ≤ lowest ever + 5% → BUY_NOW (at or near all-time low)
    - If predicted next 7 days avg > current → BUY_NOW (price will rise)
    - Otherwise → WAIT
    """
    if not predictions:
        return Recommendation(
            recommendation="INSUFFICIENT_DATA",
            confidence=0.0,
            reason="Not enough price history to make a prediction.",
            best_time_to_buy=None,
            expected_price=None,
        )

    # Next 7 days average
    next_7 = predictions[:7]
    next_7_prices = [p["predicted_price"] for p in next_7]
    avg_next_7 = float(np.mean(next_7_prices))
    min_next_7 = min(next_7_prices)

    # Next 30 days min
    min_next_30 = min(p["predicted_price"] for p in predictions[:30]) if len(predictions) >= 30 else min_next_7

    # Historical context
    avg_history = float(np.mean(prices_history)) if prices_history else current_price
    hist_low = lowest_ever or (min(prices_history) if prices_history else current_price)

    # Near all-time low?
    near_lowest = current_price <= hist_low * 1.05

    # Target price met?
    target_met = target_price is not None and current_price <= target_price

    # ── Decision Logic ────────────────────────────────────────────────────────
    if target_met:
        return Recommendation(
            recommendation="BUY_NOW",
            confidence=0.95,
            reason=f"Price has reached your target of ₹{target_price:.0f}. Buy now!",
            best_time_to_buy="Now",
            expected_price=current_price,
        )

    if near_lowest:
        return Recommendation(
            recommendation="BUY_NOW",
            confidence=0.88,
            reason=f"Current price ₹{current_price:.0f} is near the all-time low of ₹{hist_low:.0f}. This is a great time to buy.",
            best_time_to_buy="Now",
            expected_price=current_price,
        )

    pct_change_7d = (avg_next_7 - current_price) / current_price * 100

    if pct_change_7d > 3:
        # Price will increase
        best_buy_date = min(predictions[:7], key=lambda x: x["predicted_price"])["date"]
        return Recommendation(
            recommendation="BUY_NOW",
            confidence=min(0.55 + abs(pct_change_7d) / 100, 0.9),
            reason=f"Price predicted to rise by {abs(pct_change_7d):.1f}% in the next 7 days. Buy before it goes up.",
            best_time_to_buy="Now",
            expected_price=avg_next_7,
        )

    if pct_change_7d < -3:
        # Price will drop
        best_buy_date_entry = min(predictions[:30], key=lambda x: x["predicted_price"])
        return Recommendation(
            recommendation="WAIT",
            confidence=min(0.55 + abs(pct_change_7d) / 100, 0.9),
            reason=f"Price predicted to drop by {abs(pct_change_7d):.1f}% in the next 7 days. Wait for a lower price.",
            best_time_to_buy=best_buy_date_entry["date"],
            expected_price=best_buy_date_entry["predicted_price"],
        )

    # Stable price
    return Recommendation(
        recommendation="WAIT",
        confidence=0.5,
        reason="Price appears stable. Wait for a significant discount or price drop before buying.",
        best_time_to_buy=min(predictions[:30], key=lambda x: x["predicted_price"])["date"],
        expected_price=min_next_30,
    )
