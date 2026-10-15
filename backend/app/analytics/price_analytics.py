"""
Price Analytics Engine — computes all statistical metrics over price history.
"""
import statistics
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import numpy as np
from loguru import logger


class PriceAnalytics:
    """
    Stateless analytics engine.
    All methods take a list of price dicts: [{"date": ISO_str, "price": float}]
    """

    @staticmethod
    def get_summary(prices: List[float], current_price: Optional[float] = None) -> dict:
        """High-level price summary."""
        if not prices:
            return {}
        arr = np.array(prices, dtype=float)
        highest = float(arr.max())
        lowest = float(arr.min())
        avg = float(arr.mean())
        cur = current_price or prices[-1]

        # Price drop % vs highest
        price_drop_pct = round(((highest - cur) / highest) * 100, 2) if highest > cur else 0.0
        price_increase_pct = round(((cur - lowest) / lowest) * 100, 2) if cur > lowest else 0.0
        volatility = round(float(arr.std()), 2)

        return {
            "current_price": cur,
            "highest_price": highest,
            "lowest_price": lowest,
            "average_price": round(avg, 2),
            "price_drop_pct": price_drop_pct,
            "price_increase_pct": price_increase_pct,
            "volatility": volatility,
            "total_data_points": len(prices),
        }

    @staticmethod
    def get_stats(prices: List[float]) -> dict:
        """Detailed statistical measures."""
        if not prices:
            return {}
        arr = np.array(prices, dtype=float)

        # Mode
        try:
            mode_val = statistics.mode(prices)
        except statistics.StatisticsError:
            mode_val = None

        # Moving average (7-day window)
        ma7 = float(np.mean(arr[-7:])) if len(arr) >= 7 else None
        rolling30 = float(np.mean(arr[-30:])) if len(arr) >= 30 else None

        # Outlier detection (IQR method)
        q1, q3 = np.percentile(arr, [25, 75])
        iqr = q3 - q1
        outliers = arr[(arr < q1 - 1.5 * iqr) | (arr > q3 + 1.5 * iqr)]

        return {
            "mean": round(float(arr.mean()), 2),
            "median": round(float(np.median(arr)), 2),
            "mode": round(float(mode_val), 2) if mode_val else None,
            "std_dev": round(float(arr.std()), 2),
            "variance": round(float(arr.var()), 2),
            "moving_average_7d": round(ma7, 2) if ma7 else None,
            "rolling_mean_30d": round(rolling30, 2) if rolling30 else None,
            "outliers": [round(float(o), 2) for o in outliers.tolist()],
        }

    @staticmethod
    def get_trends(series: List[dict]) -> dict:
        """
        Compute weekly, monthly, and seasonal trends.
        series: [{"date": ISO, "price": float}]
        """
        if len(series) < 3:
            return {"weekly_trend": "insufficient_data", "monthly_trend": "insufficient_data"}

        prices = [s["price"] for s in series]
        n = len(prices)

        def trend_direction(window: List[float]) -> str:
            if len(window) < 2:
                return "stable"
            first_half = np.mean(window[: len(window) // 2])
            second_half = np.mean(window[len(window) // 2 :])
            delta_pct = (second_half - first_half) / first_half * 100
            if delta_pct > 2:
                return "up"
            elif delta_pct < -2:
                return "down"
            return "stable"

        weekly_data = prices[-7:] if n >= 7 else prices
        monthly_data = prices[-30:] if n >= 30 else prices

        # Seasonal: group by month
        from collections import defaultdict
        monthly_avg: dict = defaultdict(list)
        for item in series:
            try:
                dt = datetime.fromisoformat(item["date"].replace("Z", "+00:00"))
                monthly_avg[dt.month].append(item["price"])
            except Exception:
                continue

        seasonal = {m: round(np.mean(v), 2) for m, v in monthly_avg.items()}

        # Festival months (Oct=10 Diwali, Nov=11, Dec=12 Christmas)
        festival_months = {10: "Diwali", 11: "Children's Day", 12: "Christmas"}
        festival_comparison = {
            festival_months[m]: seasonal.get(m)
            for m in festival_months
            if m in seasonal
        }

        return {
            "weekly_trend": trend_direction(weekly_data),
            "monthly_trend": trend_direction(monthly_data),
            "seasonal_trend": "holiday_spike" if any(seasonal.get(m, 0) > np.mean(prices) * 1.1 for m in [10, 11, 12]) else "stable",
            "festival_comparison": festival_comparison,
        }

    @staticmethod
    def get_chart_data(series: List[dict]) -> dict:
        """Prepare data for Chart.js line charts."""
        labels = [s["date"][:10] for s in series]
        prices = [s["price"] for s in series]

        # 7-day moving average overlay
        ma_prices = []
        for i in range(len(prices)):
            window = prices[max(0, i - 6) : i + 1]
            ma_prices.append(round(float(np.mean(window)), 2))

        return {
            "labels": labels,
            "prices": prices,
            "moving_average": ma_prices,
        }

    @staticmethod
    def get_heatmap_data(series: List[dict]) -> List[dict]:
        """
        Weekly heatmap: avg price per (day_of_week, week_number).
        Returns list of {x: day_name, y: week, value: avg_price}.
        """
        from collections import defaultdict
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        cell_data: dict = defaultdict(list)

        for item in series:
            try:
                dt = datetime.fromisoformat(item["date"].replace("Z", "+00:00"))
                week_num = dt.isocalendar()[1]
                day_idx = dt.weekday()
                cell_data[(day_names[day_idx], week_num)].append(item["price"])
            except Exception:
                continue

        return [
            {"x": k[0], "y": k[1], "value": round(float(np.mean(v)), 2)}
            for k, v in cell_data.items()
        ]
