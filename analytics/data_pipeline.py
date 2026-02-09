"""Data loading, validation, and preprocessing for health CSV files.

Handles Google Fit-style CSV exports with date parsing, column validation,
missing data handling, and resampling to different time granularities.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

import pandas as pd

from config import get_settings

logger = logging.getLogger(__name__)

DatasetName = Literal["daily_activity", "heart_rate", "sleep"]

EXPECTED_COLUMNS: dict[DatasetName, list[str]] = {
    "daily_activity": ["date", "steps", "calories_burned", "distance_km", "active_minutes"],
    "heart_rate": ["timestamp", "bpm"],
    "sleep": [
        "date", "sleep_start", "sleep_end", "duration_hours",
        "deep_sleep_pct", "light_sleep_pct", "rem_pct",
    ],
}


class HealthDataLoader:
    """Load and validate health data from CSV files.

    Attributes:
        data_dir: Path to directory containing CSV files.
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or get_settings().sample_data_dir

    def load_activity(self) -> pd.DataFrame:
        """Load daily activity data with date parsing.

        Returns:
            DataFrame indexed by date with steps, calories, distance, active_minutes.
        """
        df = self._load_csv("daily_activity")
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        logger.info("Loaded activity data: %d days", len(df))
        return df

    def load_heart_rate(self) -> pd.DataFrame:
        """Load heart rate time series data.

        Returns:
            DataFrame with timestamp index and bpm column.
        """
        df = self._load_csv("heart_rate")
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)
        logger.info("Loaded heart rate data: %d measurements", len(df))
        return df

    def load_sleep(self) -> pd.DataFrame:
        """Load nightly sleep session data.

        Returns:
            DataFrame with sleep timing and stage percentages.
        """
        df = self._load_csv("sleep")
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        logger.info("Loaded sleep data: %d nights", len(df))
        return df

    def _load_csv(self, dataset: DatasetName) -> pd.DataFrame:
        """Load and validate a named CSV dataset.

        Args:
            dataset: One of 'daily_activity', 'heart_rate', 'sleep'.

        Returns:
            Raw DataFrame with validated columns.

        Raises:
            FileNotFoundError: If the CSV file doesn't exist.
            ValueError: If expected columns are missing.
        """
        path = self.data_dir / f"{dataset}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")

        df = pd.read_csv(path)
        self._validate_columns(df, dataset)
        return df

    def _validate_columns(self, df: pd.DataFrame, dataset: DatasetName) -> None:
        """Verify all expected columns are present."""
        expected = set(EXPECTED_COLUMNS[dataset])
        actual = set(df.columns)
        missing = expected - actual
        if missing:
            raise ValueError(f"Missing columns in {dataset}: {missing}")


def resample_activity_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """Resample daily activity data to weekly aggregates.

    Args:
        df: Daily activity DataFrame with 'date' column.

    Returns:
        Weekly aggregated DataFrame with sums and means.
    """
    df_indexed = df.set_index("date")
    weekly = df_indexed.resample("W").agg({
        "steps": "sum",
        "calories_burned": "sum",
        "distance_km": "sum",
        "active_minutes": "sum",
    })
    weekly["avg_daily_steps"] = (weekly["steps"] / 7).round(0).astype(int)
    return weekly.reset_index()


def resample_hr_hourly(df: pd.DataFrame) -> pd.DataFrame:
    """Resample heart rate data to hourly averages.

    Args:
        df: Heart rate DataFrame with 'timestamp' column.

    Returns:
        Hourly averaged heart rate data.
    """
    df_indexed = df.set_index("timestamp")
    hourly = df_indexed.resample("h").agg({"bpm": ["mean", "min", "max"]})
    hourly.columns = ["bpm_mean", "bpm_min", "bpm_max"]
    hourly = hourly.round(1)
    return hourly.reset_index()
