"""
FoodLoop AI - Demand Forecasting Subsystem
Time-series and tabular machine learning pipeline for institutional kitchens.
"""

from .predict import ForecastInferenceEngine, forecast_engine
from .model import NaiveBaselineModel, MovingAverageModel, RandomForestForecastModel, XGBoostForecastModel

__all__ = [
    "ForecastInferenceEngine",
    "forecast_engine",
    "NaiveBaselineModel",
    "MovingAverageModel",
    "RandomForestForecastModel",
    "XGBoostForecastModel",
]
