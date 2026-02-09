"""Statistical health metrics computation.

Computes rolling averages, trend analysis, anomaly detection,
and summary statistics from health data DataFrames.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ActivitySummary:
    """Aggregate activity statistics over a period."""

    mean_steps: float
    median_steps: float
    std_steps: float
    total_active_minutes: int
    avg_daily_calories: float
    total_distance_km: float
    trend_slope: float  # steps per day (positive = improving)
    trend_pvalue: float
    weekday_avg_steps: float
    weekend_avg_steps: float


@dataclass(frozen=True)
class SleepSummary:
    """Aggregate sleep statistics over a period."""

    avg_duration_hours: float
    std_duration_hours: float
    avg_deep_sleep_pct: float
    avg_rem_pct: float
    avg_light_sleep_pct: float
    bedtime_consistency: float  # std of bedtime in hours (lower = more consistent)
    weekend_shift_hours: float  # social jet lag metric


@dataclass(frozen=True)
class HeartRateSummary:
    """Aggregate heart rate statistics over a period."""

    resting_hr_mean: float
    resting_hr_std: float
    max_hr_observed: int
    time_in_zones: dict[str, float] = field(default_factory=dict)  # zone -> percentage


class HealthMetrics:
    """Compute derived health metrics from raw data.

    All methods are stateless — they take DataFrames and return
    dataclass results, making them easy to test.
    """

    def compute_activity_summary(self, df: pd.DataFrame) -> ActivitySummary:
        """Compute activity summary with trend analysis.

        Uses scipy.stats.linregress for trend detection.

        Args:
            df: Daily activity DataFrame with 'date', 'steps', etc.

        Returns:
            ActivitySummary with statistics and trend info.
        """
        x = np.arange(len(df))
        slope, _intercept, _r, p, _se = stats.linregress(x, df["steps"])

        # Weekday vs weekend
        dow = pd.to_datetime(df["date"]).dt.dayofweek
        weekday_avg = float(df.loc[dow < 5, "steps"].mean())
        weekend_avg = float(df.loc[dow >= 5, "steps"].mean())

        return ActivitySummary(
            mean_steps=float(df["steps"].mean()),
            median_steps=float(df["steps"].median()),
            std_steps=float(df["steps"].std()),
            total_active_minutes=int(df["active_minutes"].sum()),
            avg_daily_calories=float(df["calories_burned"].mean()),
            total_distance_km=float(df["distance_km"].sum()),
            trend_slope=float(slope),
            trend_pvalue=float(p),
            weekday_avg_steps=weekday_avg,
            weekend_avg_steps=weekend_avg,
        )

    def compute_sleep_summary(self, df: pd.DataFrame) -> SleepSummary:
        """Compute sleep quality summary.

        Args:
            df: Sleep DataFrame with duration, stage percentages, etc.

        Returns:
            SleepSummary with averages and consistency metrics.
        """
        # Parse bedtime hours for consistency calculation
        bedtime_parts = df["sleep_start"].str.split(":", expand=True).astype(float)
        bedtime_hours = bedtime_parts[0] + bedtime_parts[1] / 60
        # Normalize: hours >= 20 stay as-is, hours < 12 add 24 (past midnight)
        bedtime_hours = bedtime_hours.where(bedtime_hours >= 12, bedtime_hours + 24)

        # Weekend shift (social jet lag)
        dow = pd.to_datetime(df["date"]).dt.dayofweek
        weekday_bed = bedtime_hours[dow < 5].mean()
        weekend_bed = bedtime_hours[dow >= 5].mean()

        return SleepSummary(
            avg_duration_hours=float(df["duration_hours"].mean()),
            std_duration_hours=float(df["duration_hours"].std()),
            avg_deep_sleep_pct=float(df["deep_sleep_pct"].mean()),
            avg_rem_pct=float(df["rem_pct"].mean()),
            avg_light_sleep_pct=float(df["light_sleep_pct"].mean()),
            bedtime_consistency=float(bedtime_hours.std()),
            weekend_shift_hours=float(weekend_bed - weekday_bed),
        )

    def compute_hr_summary(self, df: pd.DataFrame) -> HeartRateSummary:
        """Compute heart rate summary with zone distribution.

        HR zones (standard):
        - Resting: < 70 bpm
        - Light: 70-100 bpm
        - Moderate: 100-140 bpm
        - Vigorous: > 140 bpm

        Args:
            df: Heart rate DataFrame with 'bpm' column.

        Returns:
            HeartRateSummary with resting HR and zone percentages.
        """
        total = len(df)
        zones = {
            "resting": float((df["bpm"] < 70).sum() / total * 100),
            "light": float(((df["bpm"] >= 70) & (df["bpm"] < 100)).sum() / total * 100),
            "moderate": float(((df["bpm"] >= 100) & (df["bpm"] < 140)).sum() / total * 100),
            "vigorous": float((df["bpm"] >= 140).sum() / total * 100),
        }

        # Resting HR: measurements during likely rest periods (low HR readings)
        resting_mask = df["bpm"] < 70
        resting_bpm = df.loc[resting_mask, "bpm"]

        return HeartRateSummary(
            resting_hr_mean=float(resting_bpm.mean()) if len(resting_bpm) > 0 else 0.0,
            resting_hr_std=float(resting_bpm.std()) if len(resting_bpm) > 1 else 0.0,
            max_hr_observed=int(df["bpm"].max()),
            time_in_zones=zones,
        )

    def compute_rolling_averages(
        self,
        df: pd.DataFrame,
        column: str,
        windows: list[int] | None = None,
    ) -> pd.DataFrame:
        """Add rolling average columns to a DataFrame.

        Args:
            df: Input DataFrame with a numeric column.
            column: Column name to compute rolling averages for.
            windows: Window sizes in rows. Defaults to [7, 30].

        Returns:
            DataFrame with added rolling average columns.
        """
        windows = windows or [7, 30]
        result = df.copy()
        for w in windows:
            result[f"{column}_rolling_{w}d"] = (
                result[column].rolling(window=w, min_periods=1).mean().round(1)
            )
        return result

    def detect_anomalies(
        self,
        df: pd.DataFrame,
        column: str,
        window: int = 14,
        threshold: float = 2.0,
    ) -> pd.DataFrame:
        """Detect anomalous values using rolling z-score.

        Values more than `threshold` standard deviations from the
        rolling mean are flagged as anomalies.

        Args:
            df: Input DataFrame.
            column: Column to check for anomalies.
            window: Rolling window size for baseline.
            threshold: Number of std deviations for anomaly threshold.

        Returns:
            DataFrame with 'is_anomaly' and 'z_score' columns added.
        """
        result = df.copy()
        rolling_mean = result[column].rolling(window=window, min_periods=3).mean()
        rolling_std = result[column].rolling(window=window, min_periods=3).std()

        z_scores = (result[column] - rolling_mean) / rolling_std.replace(0, np.nan)
        result["z_score"] = z_scores.round(2)
        result["is_anomaly"] = z_scores.abs() > threshold
        return result
