"""Plotly chart generators for the health analytics dashboard.

Each function returns a plotly Figure object ready for display in Streamlit.
All charts use a consistent theme via apply_theme().
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

# Consistent color palette
COLORS = {
    "primary": "#4F46E5",      # Indigo
    "secondary": "#06B6D4",    # Cyan
    "accent": "#F59E0B",       # Amber
    "success": "#10B981",      # Emerald
    "danger": "#EF4444",       # Red
    "neutral": "#6B7280",      # Gray
    "deep_sleep": "#3730A3",   # Dark indigo
    "rem_sleep": "#7C3AED",    # Purple
    "light_sleep": "#A5B4FC",  # Light indigo
}


def apply_theme(fig: go.Figure) -> go.Figure:
    """Apply consistent HealthPilot theme to a plotly figure.

    Args:
        fig: Plotly figure to style.

    Returns:
        The styled figure.
    """
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Inter, sans-serif", size=12, color="#1F2937"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def plot_steps_timeline(df: pd.DataFrame) -> go.Figure:
    """Plot daily steps over time with 7-day rolling average.

    Args:
        df: Activity DataFrame with 'date' and 'steps' columns.

    Returns:
        Line chart with raw steps and smoothed trend.
    """
    fig = go.Figure()

    # Raw daily steps
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["steps"],
        mode="markers+lines",
        name="Daily Steps",
        line=dict(color=COLORS["primary"], width=1),
        marker=dict(size=4, opacity=0.6),
        opacity=0.7,
    ))

    # 7-day rolling average
    rolling = df["steps"].rolling(window=7, min_periods=1).mean()
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=rolling,
        mode="lines",
        name="7-Day Average",
        line=dict(color=COLORS["accent"], width=3),
    ))

    # Step goal reference line
    fig.add_hline(
        y=10000, line_dash="dash", line_color=COLORS["success"],
        annotation_text="10K Goal", annotation_position="top right",
    )

    fig.update_layout(
        title="Daily Steps",
        xaxis_title="Date",
        yaxis_title="Steps",
    )
    return apply_theme(fig)


def plot_weekly_heatmap(df: pd.DataFrame) -> go.Figure:
    """Plot activity heatmap by day of week and week number.

    Args:
        df: Activity DataFrame with 'date' and 'steps' columns.

    Returns:
        Heatmap showing step intensity patterns.
    """
    df_temp = df.copy()
    df_temp["dow"] = pd.to_datetime(df_temp["date"]).dt.day_name()
    df_temp["week"] = pd.to_datetime(df_temp["date"]).dt.isocalendar().week.astype(int)

    # Pivot to heatmap format
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = df_temp.pivot_table(values="steps", index="dow", columns="week", aggfunc="mean")
    pivot = pivot.reindex(dow_order)

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[f"W{w}" for w in pivot.columns],
        y=pivot.index,
        colorscale="Blues",
        colorbar_title="Steps",
    ))

    fig.update_layout(
        title="Weekly Activity Heatmap",
        xaxis_title="Week",
        yaxis_title="Day of Week",
    )
    return apply_theme(fig)


def plot_sleep_patterns(df: pd.DataFrame) -> go.Figure:
    """Plot sleep duration with stage breakdown as stacked bars.

    Args:
        df: Sleep DataFrame with duration and stage percentage columns.

    Returns:
        Stacked bar chart showing sleep composition.
    """
    fig = go.Figure()

    # Convert percentages to hours
    deep_hours = df["duration_hours"] * df["deep_sleep_pct"] / 100
    rem_hours = df["duration_hours"] * df["rem_pct"] / 100
    light_hours = df["duration_hours"] * df["light_sleep_pct"] / 100

    fig.add_trace(go.Bar(
        x=df["date"], y=deep_hours, name="Deep Sleep",
        marker_color=COLORS["deep_sleep"],
    ))
    fig.add_trace(go.Bar(
        x=df["date"], y=rem_hours, name="REM Sleep",
        marker_color=COLORS["rem_sleep"],
    ))
    fig.add_trace(go.Bar(
        x=df["date"], y=light_hours, name="Light Sleep",
        marker_color=COLORS["light_sleep"],
    ))

    # Sleep goal reference
    fig.add_hline(
        y=8.0, line_dash="dash", line_color=COLORS["success"],
        annotation_text="8h Goal",
    )

    fig.update_layout(
        barmode="stack",
        title="Sleep Duration & Stages",
        xaxis_title="Date",
        yaxis_title="Hours",
    )
    return apply_theme(fig)


def plot_hr_zones(df: pd.DataFrame) -> go.Figure:
    """Plot heart rate zone distribution as a donut chart.

    Args:
        df: Heart rate DataFrame with 'bpm' column.

    Returns:
        Donut chart showing time in each HR zone.
    """
    total = len(df)
    zones = {
        "Resting (<70)": (df["bpm"] < 70).sum(),
        "Light (70-100)": ((df["bpm"] >= 70) & (df["bpm"] < 100)).sum(),
        "Moderate (100-140)": ((df["bpm"] >= 100) & (df["bpm"] < 140)).sum(),
        "Vigorous (>140)": (df["bpm"] >= 140).sum(),
    }

    fig = go.Figure(data=[go.Pie(
        labels=list(zones.keys()),
        values=list(zones.values()),
        hole=0.45,
        marker_colors=[
            COLORS["secondary"], COLORS["success"],
            COLORS["accent"], COLORS["danger"],
        ],
        textinfo="label+percent",
    )])

    fig.update_layout(title="Heart Rate Zone Distribution")
    return apply_theme(fig)


def plot_hr_circadian(df: pd.DataFrame) -> go.Figure:
    """Plot average heart rate by hour of day (circadian pattern).

    Args:
        df: Heart rate DataFrame with 'timestamp' and 'bpm' columns.

    Returns:
        Line chart showing HR circadian rhythm.
    """
    df_temp = df.copy()
    df_temp["hour"] = pd.to_datetime(df_temp["timestamp"]).dt.hour
    hourly = df_temp.groupby("hour")["bpm"].agg(["mean", "std"]).reset_index()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hourly["hour"],
        y=hourly["mean"],
        mode="lines+markers",
        name="Average HR",
        line=dict(color=COLORS["danger"], width=2),
        marker=dict(size=6),
    ))

    # Add std band
    fig.add_trace(go.Scatter(
        x=pd.concat([hourly["hour"], hourly["hour"][::-1]]),
        y=pd.concat([hourly["mean"] + hourly["std"],
                      (hourly["mean"] - hourly["std"])[::-1]]),
        fill="toself",
        fillcolor="rgba(239, 68, 68, 0.15)",
        line=dict(color="rgba(0,0,0,0)"),
        name="Std Dev",
    ))

    fig.update_layout(
        title="Heart Rate Circadian Pattern",
        xaxis_title="Hour of Day",
        yaxis_title="BPM",
        xaxis=dict(dtick=2, range=[-0.5, 23.5]),
    )
    return apply_theme(fig)


def plot_correlation(
    df_activity: pd.DataFrame,
    df_sleep: pd.DataFrame,
) -> go.Figure:
    """Plot correlation between sleep duration and next-day steps.

    Args:
        df_activity: Activity DataFrame with 'date' and 'steps'.
        df_sleep: Sleep DataFrame with 'date' and 'duration_hours'.

    Returns:
        Scatter plot with trendline.
    """
    # Merge: sleep on night N -> activity on day N+1
    sleep_shifted = df_sleep[["date", "duration_hours"]].copy()
    sleep_shifted["date"] = pd.to_datetime(sleep_shifted["date"]) + pd.Timedelta(days=1)

    merged = pd.merge(
        sleep_shifted,
        df_activity[["date", "steps"]],
        on="date",
        how="inner",
    )

    if len(merged) < 5:
        fig = go.Figure()
        fig.add_annotation(text="Insufficient overlapping data", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False)
        return apply_theme(fig)

    fig = px.scatter(
        merged,
        x="duration_hours",
        y="steps",
        trendline="ols",
        labels={"duration_hours": "Sleep Duration (hours)", "steps": "Next-Day Steps"},
        title="Sleep Duration vs. Next-Day Steps",
    )
    fig.update_traces(marker=dict(color=COLORS["primary"], size=8, opacity=0.7))
    return apply_theme(fig)


def plot_activity_by_day_of_week(df: pd.DataFrame) -> go.Figure:
    """Plot average steps by day of week as a bar chart.

    Args:
        df: Activity DataFrame with 'date' and 'steps'.

    Returns:
        Bar chart showing weekday vs weekend patterns.
    """
    df_temp = df.copy()
    df_temp["dow"] = pd.to_datetime(df_temp["date"]).dt.day_name()
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    avg_by_dow = df_temp.groupby("dow")["steps"].mean().reindex(dow_order)

    colors = [COLORS["primary"]] * 5 + [COLORS["accent"]] * 2

    fig = go.Figure(data=[go.Bar(
        x=avg_by_dow.index,
        y=avg_by_dow.values,
        marker_color=colors,
    )])

    fig.update_layout(
        title="Average Steps by Day of Week",
        xaxis_title="Day",
        yaxis_title="Average Steps",
    )
    return apply_theme(fig)
