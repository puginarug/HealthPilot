"""Generate realistic synthetic health data for HealthPilot demo.

Produces 90 days of data mimicking Google Fit exports with:
- Weekday/weekend patterns
- Circadian heart rate rhythms
- Gradual fitness improvement trend
- Realistic missing data and anomalies

Usage:
    python data/generate_sample_data.py
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

SAMPLE_DIR = Path(__file__).parent / "sample"
START_DATE = "2025-11-01"
N_DAYS = 90
SEED = 42


def generate_daily_activity(
    n_days: int = N_DAYS,
    start_date: str = START_DATE,
    seed: int = SEED,
) -> pd.DataFrame:
    """Generate realistic daily activity data with weekly patterns.

    Models weekday commute activity (higher steps), weekend leisure patterns,
    a gradual improvement trend (~+30 steps/day), and correlated metrics.

    Args:
        n_days: Number of days to generate.
        start_date: First date in YYYY-MM-DD format.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns: date, steps, calories_burned, distance_km, active_minutes.
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start_date, periods=n_days, freq="D")

    # Day-of-week effect: weekdays slightly higher than weekends
    dow = dates.dayofweek
    dow_factor = np.where(dow < 5, 1.0, 0.82)

    # Gradual improvement trend: ~+30 steps/day over 90 days
    trend = np.linspace(0, 2700, n_days)

    # Base steps from log-normal distribution (right-skewed, realistic)
    base_steps = rng.lognormal(mean=np.log(8200), sigma=0.30, size=n_days)
    steps = ((base_steps * dow_factor) + trend).astype(int)

    # Inject anomalies: 2 very low days (sick), 1 very high day (hiking)
    anomaly_low_idx = rng.choice(range(15, 60), size=2, replace=False)
    anomaly_high_idx = rng.choice(range(40, 80), size=1)
    steps[anomaly_low_idx] = rng.integers(800, 2000, size=2)
    steps[anomaly_high_idx] = rng.integers(22000, 28000, size=1)

    # Correlated metrics
    step_noise = rng.normal(1.0, 0.05, n_days)
    distance_km = np.round(steps * 0.00078 * step_noise, 2)
    bmr = 1850  # Assumed base metabolic rate
    calories_burned = np.round(bmr + steps * rng.normal(0.045, 0.003, n_days), 0).astype(int)
    active_minutes = np.clip(
        (steps / rng.normal(155, 15, n_days)).astype(int), 5, 150
    )

    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "steps": steps,
        "calories_burned": calories_burned,
        "distance_km": distance_km,
        "active_minutes": active_minutes,
    })

    # Remove ~5 random days to simulate missing data
    missing_idx = rng.choice(range(5, n_days - 5), size=5, replace=False)
    df = df.drop(index=missing_idx).reset_index(drop=True)

    return df


def generate_heart_rate(
    n_days: int = N_DAYS,
    start_date: str = START_DATE,
    seed: int = SEED,
) -> pd.DataFrame:
    """Generate 5-minute interval heart rate data with circadian rhythm.

    Models:
    - Circadian base: sinusoidal with nadir ~4 AM (58 bpm), peak ~3 PM (72 bpm)
    - Sleep periods (11 PM - 7 AM): lower HR
    - Exercise windows: random 30-60 min blocks with elevated HR
    - AR(1) autocorrelation (rho=0.85) for temporal smoothness

    Args:
        n_days: Number of days to generate.
        start_date: First date in YYYY-MM-DD format.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns: timestamp, bpm.
    """
    rng = np.random.default_rng(seed)
    intervals_per_day = 288  # 24 hours * 60 min / 5 min
    total_intervals = n_days * intervals_per_day

    timestamps = pd.date_range(
        start_date, periods=total_intervals, freq="5min"
    )
    hours = timestamps.hour + timestamps.minute / 60.0

    # Circadian rhythm: sinusoidal with minimum at 4 AM, peak at 3 PM
    circadian_base = 65 + 7 * np.sin(2 * np.pi * (hours - 4) / 24)

    # Sleep reduction: lower HR during 11 PM - 7 AM
    is_sleeping = ((hours >= 23) | (hours < 7)).astype(float)
    sleep_reduction = is_sleeping * rng.normal(6, 1.5, total_intervals)

    # Exercise spikes: ~1 exercise session per day, 30-60 min, during 6-9 AM or 5-8 PM
    exercise_boost = np.zeros(total_intervals)
    for day in range(n_days):
        if rng.random() < 0.6:  # 60% of days have exercise
            day_start = day * intervals_per_day
            # Choose morning (6-9 AM) or evening (5-8 PM) exercise
            if rng.random() < 0.5:
                exercise_start_hour = rng.uniform(6, 8)
            else:
                exercise_start_hour = rng.uniform(17, 19)
            exercise_start_idx = day_start + int(exercise_start_hour * 12)
            exercise_duration = rng.integers(6, 12)  # 30-60 min in 5-min intervals
            end_idx = min(exercise_start_idx + exercise_duration, total_intervals)
            # Ramp up, plateau, ramp down
            for i in range(exercise_start_idx, end_idx):
                progress = (i - exercise_start_idx) / exercise_duration
                if progress < 0.2:
                    exercise_boost[i] = 40 * (progress / 0.2)
                elif progress > 0.85:
                    exercise_boost[i] = 40 * ((1 - progress) / 0.15)
                else:
                    exercise_boost[i] = rng.normal(40, 8)

    # Combine components
    target_hr = circadian_base - sleep_reduction + exercise_boost

    # AR(1) process for temporal smoothness
    rho = 0.85
    bpm = np.zeros(total_intervals)
    bpm[0] = target_hr[0] + rng.normal(0, 2)
    for i in range(1, total_intervals):
        innovation = rng.normal(0, 2.5)
        bpm[i] = target_hr[i] + rho * (bpm[i - 1] - target_hr[i - 1]) + innovation

    # Clip to physiological range
    bpm = np.clip(bpm, 42, 195).astype(int)

    df = pd.DataFrame({
        "timestamp": timestamps.strftime("%Y-%m-%dT%H:%M:%S"),
        "bpm": bpm,
    })

    return df


def generate_sleep(
    n_days: int = N_DAYS,
    start_date: str = START_DATE,
    seed: int = SEED,
) -> pd.DataFrame:
    """Generate nightly sleep data with realistic patterns.

    Models:
    - Bedtime: Normal(23.25, 0.6) hours, weekend shift +0.5h
    - Wake time: Normal(7.0, 0.4) hours, weekend shift +0.75h
    - Sleep stages: deep ~18-22%, REM ~22-25%, light = remainder
    - Social jet lag on weekends

    Args:
        n_days: Number of days (nights) to generate.
        start_date: First date in YYYY-MM-DD format.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns: date, sleep_start, sleep_end, duration_hours,
        deep_sleep_pct, light_sleep_pct, rem_pct.
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start_date, periods=n_days, freq="D")

    records: list[dict] = []

    for i, date in enumerate(dates):
        dow = date.dayofweek

        # Weekend shift: later bedtime and wake time
        is_weekend = dow >= 4  # Friday and Saturday nights
        bed_shift = 0.5 if is_weekend else 0.0
        wake_shift = 0.75 if is_weekend else 0.0

        # Bedtime: around 11:15 PM +/- 36 min
        bedtime_hour = rng.normal(23.25 + bed_shift, 0.6)
        bedtime_hour = np.clip(bedtime_hour, 21.5, 25.5)  # Allow past midnight

        # Wake time: around 7:00 AM +/- 24 min
        wake_hour = rng.normal(7.0 + wake_shift, 0.4)
        wake_hour = np.clip(wake_hour, 5.5, 9.5)

        # Duration
        if bedtime_hour >= 24:
            duration = wake_hour + (24 - bedtime_hour)
        else:
            duration = wake_hour + (24 - bedtime_hour)
        duration = round(duration, 2)

        # Sleep stages (must sum to ~100%, allow small rounding)
        deep_pct = round(rng.normal(20, 3), 1)
        rem_pct = round(rng.normal(23, 2.5), 1)
        deep_pct = float(np.clip(deep_pct, 10, 30))
        rem_pct = float(np.clip(rem_pct, 15, 32))
        light_pct = round(100 - deep_pct - rem_pct, 1)

        # Format times
        bed_h = int(bedtime_hour) % 24
        bed_m = int((bedtime_hour % 1) * 60)
        wake_h = int(wake_hour)
        wake_m = int((wake_hour % 1) * 60)

        sleep_start = f"{bed_h:02d}:{bed_m:02d}"
        sleep_end = f"{wake_h:02d}:{wake_m:02d}"

        records.append({
            "date": date.strftime("%Y-%m-%d"),
            "sleep_start": sleep_start,
            "sleep_end": sleep_end,
            "duration_hours": duration,
            "deep_sleep_pct": deep_pct,
            "light_sleep_pct": light_pct,
            "rem_pct": rem_pct,
        })

    df = pd.DataFrame(records)

    # Remove ~3 random nights (missing data)
    missing_idx = rng.choice(range(3, n_days - 3), size=3, replace=False)
    df = df.drop(index=missing_idx).reset_index(drop=True)

    return df


def main() -> None:
    """Generate all sample data files and write to data/sample/."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Generating daily activity data...")
    activity_df = generate_daily_activity()
    activity_path = SAMPLE_DIR / "daily_activity.csv"
    activity_df.to_csv(activity_path, index=False)
    logger.info("  Wrote %d rows to %s", len(activity_df), activity_path)

    logger.info("Generating heart rate data...")
    hr_df = generate_heart_rate()
    hr_path = SAMPLE_DIR / "heart_rate.csv"
    hr_df.to_csv(hr_path, index=False)
    logger.info("  Wrote %d rows to %s", len(hr_df), hr_path)

    logger.info("Generating sleep data...")
    sleep_df = generate_sleep()
    sleep_path = SAMPLE_DIR / "sleep.csv"
    sleep_df.to_csv(sleep_path, index=False)
    logger.info("  Wrote %d rows to %s", len(sleep_df), sleep_path)

    logger.info("Sample data generation complete.")


if __name__ == "__main__":
    main()
