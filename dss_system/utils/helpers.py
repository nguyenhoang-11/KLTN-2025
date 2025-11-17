"""Helper utility functions"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timedelta


def calculate_service_level(actual_demand: pd.Series, fulfilled_demand: pd.Series) -> float:
    """Calculate fill rate service level"""
    total_demand = actual_demand.sum()
    total_fulfilled = fulfilled_demand.sum()
    if total_demand == 0:
        return 1.0
    return total_fulfilled / total_demand


def calculate_inventory_turnover(cost_of_goods_sold: float, avg_inventory_value: float) -> float:
    """Calculate inventory turnover ratio"""
    if avg_inventory_value == 0:
        return 0.0
    return cost_of_goods_sold / avg_inventory_value


def calculate_safety_stock(avg_demand: float, std_demand: float,
                          service_level: float = 0.95, lead_time_days: int = 7) -> float:
    """Calculate safety stock using normal distribution"""
    from scipy import stats
    z_score = stats.norm.ppf(service_level)
    safety_stock = z_score * std_demand * np.sqrt(lead_time_days)
    return max(0, safety_stock)


def calculate_eoq(annual_demand: float, ordering_cost: float, holding_cost_rate: float,
                  unit_cost: float) -> float:
    """Calculate Economic Order Quantity"""
    if holding_cost_rate == 0 or unit_cost == 0:
        return 0.0
    holding_cost = holding_cost_rate * unit_cost
    eoq = np.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
    return eoq


def calculate_reorder_point(avg_daily_demand: float, lead_time_days: float,
                           safety_stock: float) -> float:
    """Calculate reorder point"""
    return (avg_daily_demand * lead_time_days) + safety_stock


def format_currency(value: float) -> str:
    """Format value as currency"""
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Format value as percentage"""
    return f"{value:.2%}"


def convert_to_json_serializable(obj: Any) -> Any:
    """Convert object to JSON serializable format"""
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    return obj


def aggregate_by_time_period(df: pd.DataFrame, date_column: str,
                             value_column: str, period: str = 'D') -> pd.DataFrame:
    """Aggregate data by time period (D=daily, W=weekly, M=monthly)"""
    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column])
    result = df.groupby(pd.Grouper(key=date_column, freq=period))[value_column].sum().reset_index()
    return result


def calculate_cv(data: pd.Series) -> float:
    """Calculate coefficient of variation"""
    mean = data.mean()
    if mean == 0:
        return 0.0
    return data.std() / mean


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula (in km)"""
    R = 6371  # Earth radius in km

    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)

    a = (np.sin(dlat/2)**2 +
         np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2)
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

    return R * c
