"""
ML Pipeline — trains Linear Regression, Random Forest, and XGBoost on price history.
Generates predictions, evaluates models, and selects the best one.
"""
import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from loguru import logger

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not installed. Skipping XGBoost model.")

from app.core.config import settings


def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Feature engineering from a DataFrame with columns: date, price.
    Adds: day_of_week, month, day_of_year, week_of_year,
          lag_1, lag_7, lag_30, rolling_mean_7, rolling_std_7.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], format="ISO8601", utc=True)
    df = df.sort_values("date").reset_index(drop=True)

    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["day_of_year"] = df["date"].dt.dayofyear
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["day_index"] = range(len(df))  # Sequential index

    # Lag features
    df["lag_1"] = df["price"].shift(1)
    df["lag_7"] = df["price"].shift(7)
    df["lag_30"] = df["price"].shift(30)

    # Rolling features
    df["rolling_mean_7"] = df["price"].rolling(7, min_periods=1).mean()
    df["rolling_std_7"] = df["price"].rolling(7, min_periods=1).std().fillna(0)
    df["rolling_mean_30"] = df["price"].rolling(30, min_periods=1).mean()

    # Fill NaN lags with mean
    df = df.fillna(df["price"].mean())
    return df


FEATURE_COLS = [
    "day_of_week", "month", "day_of_year", "week_of_year", "day_index",
    "lag_1", "lag_7", "lag_30", "rolling_mean_7", "rolling_std_7", "rolling_mean_30",
]


class PricePredictor:
    """
    Trains and evaluates multiple ML models on price history.
    Saves the best model to disk for future predictions.
    """

    def __init__(self, product_id: str):
        self.product_id = product_id
        self.model_dir = os.path.join(settings.ML_MODELS_DIR, product_id)
        os.makedirs(self.model_dir, exist_ok=True)
        self.scaler = StandardScaler()

    def train_and_evaluate(self, series: List[dict]) -> dict:
        """
        Train all models; return comparison dict + best model name.
        series: [{"date": ISO_str, "price": float}]
        """
        if len(series) < settings.MIN_HISTORY_POINTS:
            return {"error": f"Need at least {settings.MIN_HISTORY_POINTS} data points. Got {len(series)}."}

        df = _engineer_features(pd.DataFrame(series))
        X = df[FEATURE_COLS].values
        y = df["price"].values

        # Scale
        X_scaled = self.scaler.fit_transform(X)
        joblib.dump(self.scaler, os.path.join(self.model_dir, "scaler.pkl"))

        # Split
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

        # ── Models ────────────────────────────────────────────────────────────
        models: dict = {
            "LinearRegression": LinearRegression(),
            "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        }
        if XGBOOST_AVAILABLE:
            models["XGBoost"] = XGBRegressor(n_estimators=100, random_state=42, verbosity=0)

        results: dict = {}
        best_model_name = None
        best_mae = float("inf")

        for name, model in models.items():
            try:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)

                mae = float(mean_absolute_error(y_test, y_pred))
                rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
                r2 = float(r2_score(y_test, y_pred))

                results[name] = {"mae": round(mae, 2), "rmse": round(rmse, 2), "r2": round(r2, 4)}

                # Save model
                joblib.dump(model, os.path.join(self.model_dir, f"{name}.pkl"))

                if mae < best_mae:
                    best_mae = mae
                    best_model_name = name

                logger.info(f"[ML][{self.product_id}] {name}: MAE={mae:.2f} RMSE={rmse:.2f} R²={r2:.4f}")

            except Exception as e:
                logger.error(f"[ML] Training {name} failed: {e}")
                results[name] = {"error": str(e)}

        # Save metadata
        meta = {"best_model": best_model_name, "trained_at": datetime.now(timezone.utc).isoformat()}
        joblib.dump(meta, os.path.join(self.model_dir, "meta.pkl"))

        return {
            "model_comparison": results,
            "best_model": best_model_name,
            "trained_on": len(series),
        }

    def predict_future(self, series: List[dict], days: int = 30) -> List[dict]:
        """
        Predict next `days` prices using the best saved model.
        Returns [{"date": "YYYY-MM-DD", "predicted_price": float}]
        """
        meta_path = os.path.join(self.model_dir, "meta.pkl")
        scaler_path = os.path.join(self.model_dir, "scaler.pkl")
        if not os.path.exists(meta_path):
            return []

        meta = joblib.load(meta_path)
        best_model_name = meta.get("best_model")
        if not best_model_name:
            return []

        model_path = os.path.join(self.model_dir, f"{best_model_name}.pkl")
        if not os.path.exists(model_path):
            return []

        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)

        # Build full df
        df = _engineer_features(pd.DataFrame(series))
        prices = list(df["price"].values)
        last_date = df["date"].iloc[-1]

        predictions = []
        for i in range(1, days + 1):
            future_date = last_date + timedelta(days=i)
            day_index = len(df) + i - 1

            lag_1 = prices[-1]
            lag_7 = prices[-7] if len(prices) >= 7 else np.mean(prices)
            lag_30 = prices[-30] if len(prices) >= 30 else np.mean(prices)
            rolling_mean_7 = float(np.mean(prices[-7:]))
            rolling_std_7 = float(np.std(prices[-7:])) if len(prices) >= 2 else 0.0
            rolling_mean_30 = float(np.mean(prices[-30:]))

            features = np.array([[
                future_date.dayofweek,
                future_date.month,
                future_date.dayofyear,
                future_date.isocalendar()[1],
                day_index,
                lag_1, lag_7, lag_30,
                rolling_mean_7, rolling_std_7, rolling_mean_30,
            ]])

            features_scaled = scaler.transform(features)
            pred_price = float(model.predict(features_scaled)[0])
            pred_price = max(0, pred_price)  # No negative prices

            prices.append(pred_price)
            predictions.append({
                "date": future_date.strftime("%Y-%m-%d"),
                "predicted_price": round(pred_price, 2),
            })

        return predictions

    def find_best_buy_date(self, predictions: List[dict]) -> Optional[str]:
        """Return the date with the lowest predicted price."""
        if not predictions:
            return None
        best = min(predictions, key=lambda x: x["predicted_price"])
        return best["date"]
