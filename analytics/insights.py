"""Rule-based health insight generation.

Analyzes computed metrics against evidence-based thresholds
(WHO guidelines, sleep science) to produce actionable insights.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from analytics.health_metrics import ActivitySummary, HeartRateSummary, SleepSummary

logger = logging.getLogger(__name__)


@dataclass
class Insight:
    """A single health insight with context and recommendation.

    Attributes:
        category: Which health domain this insight belongs to.
        severity: How urgent the insight is.
        title: Short summary (for display as heading).
        description: Detailed explanation with data.
        recommendation: Actionable next step.
    """

    category: Literal["activity", "sleep", "heart_rate"]
    severity: Literal["info", "positive", "warning", "alert"]
    title: str
    description: str
    recommendation: str


class InsightEngine:
    """Generate rule-based insights from health metric summaries.

    Thresholds are based on:
    - WHO physical activity guidelines (150 min/week moderate activity)
    - Sleep Foundation recommendations (7-9 hours for adults)
    - American Heart Association resting HR guidelines
    """

    def analyze_activity(self, summary: ActivitySummary) -> list[Insight]:
        """Generate insights from activity metrics.

        Args:
            summary: Computed activity statistics.

        Returns:
            List of relevant insights.
        """
        insights: list[Insight] = []

        # Step count assessment
        if summary.mean_steps >= 10000:
            insights.append(Insight(
                category="activity",
                severity="positive",
                title="Meeting step goals",
                description=(
                    f"Your average of {summary.mean_steps:,.0f} steps/day meets the "
                    f"10,000-step target. Research suggests this level is associated "
                    f"with reduced cardiovascular risk."
                ),
                recommendation="Maintain your current activity level.",
            ))
        elif summary.mean_steps >= 7000:
            insights.append(Insight(
                category="activity",
                severity="info",
                title="Good step count",
                description=(
                    f"Your average of {summary.mean_steps:,.0f} steps/day is above "
                    f"the 7,000-step threshold associated with reduced all-cause "
                    f"mortality (Paluch et al., 2021)."
                ),
                recommendation=(
                    f"To reach 10K, try adding a {(10000 - summary.mean_steps) / 2000:.0f}-"
                    f"minute walk to your routine."
                ),
            ))
        else:
            insights.append(Insight(
                category="activity",
                severity="warning",
                title="Below recommended daily steps",
                description=(
                    f"Your average of {summary.mean_steps:,.0f} steps/day is below "
                    f"the 7,000-step threshold associated with reduced mortality risk."
                ),
                recommendation="Start with adding a 15-minute walk after meals.",
            ))

        # Trend analysis
        if summary.trend_slope > 20 and summary.trend_pvalue < 0.05:
            insights.append(Insight(
                category="activity",
                severity="positive",
                title="Improving activity trend",
                description=(
                    f"Your step count is increasing by ~{summary.trend_slope:.0f} "
                    f"steps/day (p={summary.trend_pvalue:.3f}). "
                    f"This is a statistically significant positive trend."
                ),
                recommendation="Keep up the momentum.",
            ))
        elif summary.trend_slope < -20 and summary.trend_pvalue < 0.05:
            insights.append(Insight(
                category="activity",
                severity="alert",
                title="Declining activity trend",
                description=(
                    f"Your step count is declining by ~{abs(summary.trend_slope):.0f} "
                    f"steps/day (p={summary.trend_pvalue:.3f})."
                ),
                recommendation="Consider setting incremental daily step goals.",
            ))

        # Weekday vs weekend gap
        gap = summary.weekday_avg_steps - summary.weekend_avg_steps
        if gap > 3000:
            insights.append(Insight(
                category="activity",
                severity="info",
                title="Large weekday-weekend activity gap",
                description=(
                    f"You average {summary.weekday_avg_steps:,.0f} steps on weekdays "
                    f"vs {summary.weekend_avg_steps:,.0f} on weekends "
                    f"(a {gap:,.0f}-step difference)."
                ),
                recommendation="Try adding weekend activities like walking or cycling.",
            ))

        return insights

    def analyze_sleep(self, summary: SleepSummary) -> list[Insight]:
        """Generate insights from sleep metrics.

        Args:
            summary: Computed sleep statistics.

        Returns:
            List of relevant insights.
        """
        insights: list[Insight] = []

        # Duration assessment
        if 7.0 <= summary.avg_duration_hours <= 9.0:
            insights.append(Insight(
                category="sleep",
                severity="positive",
                title="Healthy sleep duration",
                description=(
                    f"Your average sleep of {summary.avg_duration_hours:.1f} hours "
                    f"falls within the 7-9 hour range recommended by the National "
                    f"Sleep Foundation for adults."
                ),
                recommendation="Maintain your current sleep schedule.",
            ))
        elif summary.avg_duration_hours < 7.0:
            insights.append(Insight(
                category="sleep",
                severity="warning",
                title="Insufficient sleep duration",
                description=(
                    f"Your average of {summary.avg_duration_hours:.1f} hours is below "
                    f"the 7-hour minimum. Chronic sleep restriction is linked to "
                    f"impaired cognitive function and metabolic health."
                ),
                recommendation="Try moving your bedtime 15-30 minutes earlier.",
            ))

        # Consistency
        if summary.bedtime_consistency > 1.0:
            insights.append(Insight(
                category="sleep",
                severity="warning",
                title="Inconsistent bedtime",
                description=(
                    f"Your bedtime varies by ~{summary.bedtime_consistency * 60:.0f} "
                    f"minutes (std dev). Irregular sleep schedules can disrupt "
                    f"circadian rhythm."
                ),
                recommendation="Aim for the same bedtime within a 30-minute window.",
            ))

        # Social jet lag
        if abs(summary.weekend_shift_hours) > 1.0:
            insights.append(Insight(
                category="sleep",
                severity="info",
                title="Social jet lag detected",
                description=(
                    f"Your weekend bedtime is ~{summary.weekend_shift_hours:.1f} hours "
                    f"later than weekdays. This 'social jet lag' can impair Monday "
                    f"alertness and metabolic regulation."
                ),
                recommendation="Reduce weekend bedtime shifts to under 1 hour.",
            ))

        # Deep sleep
        if summary.avg_deep_sleep_pct < 15:
            insights.append(Insight(
                category="sleep",
                severity="warning",
                title="Low deep sleep percentage",
                description=(
                    f"Your average deep sleep of {summary.avg_deep_sleep_pct:.1f}% "
                    f"is below the typical 15-20% range. Deep sleep is critical "
                    f"for physical recovery and immune function."
                ),
                recommendation="Avoid alcohol and heavy meals before bed.",
            ))

        return insights

    def analyze_heart_rate(self, summary: HeartRateSummary) -> list[Insight]:
        """Generate insights from heart rate metrics.

        Args:
            summary: Computed heart rate statistics.

        Returns:
            List of relevant insights.
        """
        insights: list[Insight] = []

        # Resting HR assessment
        if summary.resting_hr_mean < 60:
            insights.append(Insight(
                category="heart_rate",
                severity="positive",
                title="Excellent resting heart rate",
                description=(
                    f"Your resting HR of {summary.resting_hr_mean:.0f} bpm indicates "
                    f"strong cardiovascular fitness. Athletes typically have resting "
                    f"HR in the 40-60 bpm range."
                ),
                recommendation="Maintain your cardiovascular training.",
            ))
        elif summary.resting_hr_mean <= 80:
            insights.append(Insight(
                category="heart_rate",
                severity="info",
                title="Normal resting heart rate",
                description=(
                    f"Your resting HR of {summary.resting_hr_mean:.0f} bpm is within "
                    f"the normal range (60-100 bpm per AHA guidelines)."
                ),
                recommendation="Regular aerobic exercise can further lower resting HR.",
            ))
        else:
            insights.append(Insight(
                category="heart_rate",
                severity="warning",
                title="Elevated resting heart rate",
                description=(
                    f"Your resting HR of {summary.resting_hr_mean:.0f} bpm is on "
                    f"the higher end. Sustained elevated resting HR may indicate "
                    f"stress, dehydration, or insufficient recovery."
                ),
                recommendation="Ensure adequate hydration and stress management.",
            ))

        return insights

    def get_all_insights(
        self,
        activity: ActivitySummary | None = None,
        sleep: SleepSummary | None = None,
        heart_rate: HeartRateSummary | None = None,
    ) -> list[Insight]:
        """Collect all insights across health domains.

        Args:
            activity: Activity summary (optional).
            sleep: Sleep summary (optional).
            heart_rate: Heart rate summary (optional).

        Returns:
            Combined list of all generated insights.
        """
        all_insights: list[Insight] = []
        if activity:
            all_insights.extend(self.analyze_activity(activity))
        if sleep:
            all_insights.extend(self.analyze_sleep(sleep))
        if heart_rate:
            all_insights.extend(self.analyze_heart_rate(heart_rate))
        logger.info("Generated %d insights", len(all_insights))
        return all_insights
