"""Health Analytics Dashboard page.

Displays interactive charts and KPIs computed from wearable health data.
Showcases data analysis capabilities: trends, anomalies, correlations.
"""

from __future__ import annotations

import logging

import streamlit as st

from analytics.data_pipeline import HealthDataLoader
from analytics.health_metrics import HealthMetrics
from analytics.insights import InsightEngine
from analytics.visualizations import (
    plot_activity_by_day_of_week,
    plot_correlation,
    plot_hr_circadian,
    plot_hr_zones,
    plot_sleep_patterns,
    plot_steps_timeline,
    plot_weekly_heatmap,
)

logger = logging.getLogger(__name__)

st.header("Health Analytics Dashboard")
st.caption("Data-driven insights from your wearable health data")

# Sidebar for data upload
with st.sidebar:
    st.subheader("📁 Data Management")

    with st.expander("Upload Your Data", expanded=False):
        st.markdown("Upload CSV files to replace sample data:")

        activity_upload = st.file_uploader(
            "Activity Data (steps, calories, distance)",
            type="csv",
            key="activity_upload",
            help="CSV with columns: date, steps, calories_burned, distance_km, active_minutes"
        )

        sleep_upload = st.file_uploader(
            "Sleep Data",
            type="csv",
            key="sleep_upload",
            help="CSV with columns: date, sleep_start, sleep_end, duration_hours, deep_sleep_pct, light_sleep_pct, rem_pct"
        )

        hr_upload = st.file_uploader(
            "Heart Rate Data",
            type="csv",
            key="hr_upload",
            help="CSV with columns: timestamp, bpm"
        )

        if st.button("💾 Save Uploaded Files", use_container_width=True):
            import pandas as pd
            from pathlib import Path

            data_dir = Path("data/sample")
            saved_files = []

            if activity_upload:
                try:
                    df = pd.read_csv(activity_upload)
                    df.to_csv(data_dir / "daily_activity.csv", index=False)
                    saved_files.append("activity")
                    st.session_state.pop("load_all_data", None)  # Clear cache
                except Exception as e:
                    st.error(f"Error saving activity data: {e}")

            if sleep_upload:
                try:
                    df = pd.read_csv(sleep_upload)
                    df.to_csv(data_dir / "sleep.csv", index=False)
                    saved_files.append("sleep")
                    st.session_state.pop("load_all_data", None)
                except Exception as e:
                    st.error(f"Error saving sleep data: {e}")

            if hr_upload:
                try:
                    df = pd.read_csv(hr_upload)
                    df.to_csv(data_dir / "heart_rate.csv", index=False)
                    saved_files.append("heart rate")
                    st.session_state.pop("load_all_data", None)
                except Exception as e:
                    st.error(f"Error saving heart rate data: {e}")

            if saved_files:
                st.success(f"✅ Saved: {', '.join(saved_files)}")
                st.info("Refresh the page to see your new data.")
            else:
                st.warning("No files to save. Upload files first.")

    st.divider()
    st.caption("Using sample data by default")


@st.cache_data
def load_all_data() -> tuple:
    """Load all datasets with caching."""
    loader = HealthDataLoader()
    activity = loader.load_activity()
    sleep = loader.load_sleep()
    heart_rate = loader.load_heart_rate()
    return activity, sleep, heart_rate


try:
    activity_df, sleep_df, hr_df = load_all_data()
except FileNotFoundError as e:
    st.error(f"Data not found: {e}")
    st.info("Run `python data/generate_sample_data.py` to generate sample data, or upload your own files using the sidebar.")
    st.stop()

# --- Period selector ---
col_period, col_info = st.columns([1, 3])
with col_period:
    period = st.selectbox("Period", ["All", "Last 30 Days", "Last 7 Days"])

# Filter data based on period
if period == "Last 7 Days":
    cutoff = activity_df["date"].max() - __import__("pandas").Timedelta(days=7)
    activity_filtered = activity_df[activity_df["date"] >= cutoff]
    sleep_filtered = sleep_df[sleep_df["date"] >= cutoff.date()]
    hr_cutoff = hr_df["timestamp"].max() - __import__("pandas").Timedelta(days=7)
    hr_filtered = hr_df[hr_df["timestamp"] >= hr_cutoff]
elif period == "Last 30 Days":
    cutoff = activity_df["date"].max() - __import__("pandas").Timedelta(days=30)
    activity_filtered = activity_df[activity_df["date"] >= cutoff]
    sleep_filtered = sleep_df[sleep_df["date"] >= cutoff.date()]
    hr_cutoff = hr_df["timestamp"].max() - __import__("pandas").Timedelta(days=30)
    hr_filtered = hr_df[hr_df["timestamp"] >= hr_cutoff]
else:
    activity_filtered = activity_df
    sleep_filtered = sleep_df
    hr_filtered = hr_df

# --- Compute metrics ---
metrics = HealthMetrics()
activity_summary = metrics.compute_activity_summary(activity_filtered)
sleep_summary = metrics.compute_sleep_summary(sleep_filtered)
hr_summary = metrics.compute_hr_summary(hr_filtered)

# --- KPI Cards ---
st.subheader("Key Metrics")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric(
        "Avg Daily Steps",
        f"{activity_summary.mean_steps:,.0f}",
        delta=f"{activity_summary.trend_slope:+.0f}/day" if activity_summary.trend_pvalue < 0.1 else None,
    )
with kpi2:
    st.metric(
        "Avg Sleep",
        f"{sleep_summary.avg_duration_hours:.1f}h",
        delta=f"{sleep_summary.avg_deep_sleep_pct:.0f}% deep",
    )
with kpi3:
    st.metric(
        "Resting HR",
        f"{hr_summary.resting_hr_mean:.0f} bpm",
    )
with kpi4:
    st.metric(
        "Active Minutes",
        f"{activity_summary.total_active_minutes:,}",
        delta=f"{activity_summary.total_active_minutes / len(activity_filtered):.0f}/day avg",
    )

st.divider()

# --- Charts ---
st.subheader("Activity")
col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(plot_steps_timeline(activity_filtered), use_container_width=True)
with col2:
    st.plotly_chart(plot_activity_by_day_of_week(activity_filtered), use_container_width=True)

st.subheader("Sleep")
col3, col4 = st.columns(2)

with col3:
    st.plotly_chart(plot_sleep_patterns(sleep_filtered), use_container_width=True)
with col4:
    st.plotly_chart(plot_correlation(activity_filtered, sleep_filtered), use_container_width=True)

st.subheader("Heart Rate")
col5, col6 = st.columns(2)

with col5:
    st.plotly_chart(plot_hr_circadian(hr_filtered), use_container_width=True)
with col6:
    st.plotly_chart(plot_hr_zones(hr_filtered), use_container_width=True)

# --- Additional Charts ---
with st.expander("Weekly Activity Heatmap"):
    st.plotly_chart(plot_weekly_heatmap(activity_filtered), use_container_width=True)

# --- Insights ---
st.divider()
st.subheader("Insights")

engine = InsightEngine()
insights = engine.get_all_insights(activity_summary, sleep_summary, hr_summary)

if not insights:
    st.info("No notable insights for the selected period.")
else:
    for insight in insights:
        severity_icons = {
            "positive": ":material/check_circle:",
            "info": ":material/info:",
            "warning": ":material/warning:",
            "alert": ":material/error:",
        }
        icon = severity_icons.get(insight.severity, ":material/info:")

        with st.container(border=True):
            st.markdown(f"**{icon} {insight.title}**")
            st.write(insight.description)
            st.caption(f"Recommendation: {insight.recommendation}")
