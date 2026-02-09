"""Workout plan generator with LLM-powered structured workout creation.

Mirrors the meal planning architecture with Exercise, WorkoutSession, and WorkoutPlan dataclasses.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from llm_factory import create_chat_llm

logger = logging.getLogger(__name__)


@dataclass
class Exercise:
    """Single exercise specification."""

    name: str
    description: str
    sets: int
    reps: str  # Supports ranges like "8-10" or single values like "12"
    rest_seconds: int
    tempo: str | None  # Optional: "3-0-1-0" (eccentric-pause-concentric-pause)
    notes: list[str]
    equipment: list[str]
    muscle_groups: list[str]

    @property
    def estimated_duration_min(self) -> int:
        """Calculate exercise duration including rest.

        Estimates based on:
        - 3 seconds per rep (average tempo)
        - Rest periods between sets
        """
        # Parse reps to get average
        if "-" in self.reps:
            try:
                rep_range = self.reps.split("-")
                avg_reps = (int(rep_range[0]) + int(rep_range[1])) / 2
            except ValueError:
                avg_reps = 10  # Default fallback
        else:
            try:
                avg_reps = int(self.reps) if self.reps.isdigit() else 10
            except ValueError:
                avg_reps = 10

        # Estimate work time: 3 sec per rep
        work_time_sec = self.sets * (avg_reps * 3)
        # Rest time between sets (exclude rest after last set)
        rest_time_sec = (self.sets - 1) * self.rest_seconds

        total_seconds = work_time_sec + rest_time_sec
        return round(total_seconds / 60)  # Convert to minutes


@dataclass
class WorkoutSession:
    """Single workout session specification."""

    day_name: str  # "Day 1: Push" or "Monday"
    focus: str  # "Upper Body Push" or "Lower Body Strength"
    exercises: list[Exercise]
    warmup_notes: list[str]
    cooldown_notes: list[str]

    @property
    def total_duration_min(self) -> int:
        """Calculate total session duration."""
        warmup = 10  # Standard warmup time
        cooldown = 10  # Standard cooldown time
        exercise_time = sum(ex.estimated_duration_min for ex in self.exercises)
        return warmup + exercise_time + cooldown

    @property
    def total_sets(self) -> int:
        """Total number of sets in session."""
        return sum(ex.sets for ex in self.exercises)

    @property
    def muscle_groups_targeted(self) -> list[str]:
        """Get unique muscle groups targeted in this session."""
        groups = set()
        for ex in self.exercises:
            groups.update(ex.muscle_groups)
        return sorted(list(groups))


@dataclass
class WorkoutPlan:
    """Complete multi-week workout plan."""

    weeks: list[list[WorkoutSession]]  # List of weeks, each containing sessions
    fitness_level: str  # "beginner" | "intermediate" | "advanced"
    goals: list[str]  # ["strength", "hypertrophy", "endurance"]
    days_per_week: int  # 3-6
    session_duration_min: int  # 30/45/60/90
    equipment: list[str]  # ["bodyweight", "dumbbells", "barbell"]
    restrictions: list[str]  # ["lower back injury", "no jumping"]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "fitness_level": self.fitness_level,
            "goals": self.goals,
            "days_per_week": self.days_per_week,
            "session_duration_min": self.session_duration_min,
            "equipment": self.equipment,
            "restrictions": self.restrictions,
            "weeks": [
                [
                    {
                        "day_name": session.day_name,
                        "focus": session.focus,
                        "warmup_notes": session.warmup_notes,
                        "cooldown_notes": session.cooldown_notes,
                        "exercises": [asdict(ex) for ex in session.exercises],
                        "totals": {
                            "duration_min": session.total_duration_min,
                            "total_sets": session.total_sets,
                            "muscle_groups": session.muscle_groups_targeted,
                        },
                    }
                    for session in week
                ]
                for week in self.weeks
            ],
        }


class WorkoutPlanGenerator:
    """Generate structured workout plans using LLM with exercise science principles."""

    def __init__(self) -> None:
        """Initialize the workout plan generator."""
        self.llm = create_chat_llm(temperature=0.7)  # Creative for workout variety

    def generate(
        self,
        weeks: int,
        fitness_level: str,
        goals: list[str],
        days_per_week: int,
        session_duration_min: int,
        equipment: list[str],
        restrictions: list[str],
        user_profile: dict | None = None,
    ) -> WorkoutPlan:
        """Generate a structured workout plan.

        Args:
            weeks: Number of weeks to generate (1-4)
            fitness_level: beginner/intermediate/advanced
            goals: List of goals (strength, hypertrophy, endurance, weight_loss, flexibility)
            days_per_week: 3-6 workout days per week
            session_duration_min: Target duration (30/45/60/90 minutes)
            equipment: Available equipment list
            restrictions: Injuries or limitations to work around
            user_profile: Optional user profile data

        Returns:
            WorkoutPlan with structured weeks/sessions/exercises
        """
        logger.info(
            "Generating %d-week workout plan: %s level, %d days/week, %d min/session",
            weeks,
            fitness_level,
            days_per_week,
            session_duration_min,
        )

        # Build system prompt with exercise science context
        system_prompt = self._build_system_prompt()

        # Build user prompt with specific parameters
        user_prompt = self._build_user_prompt(
            weeks=weeks,
            fitness_level=fitness_level,
            goals=goals,
            days_per_week=days_per_week,
            session_duration_min=session_duration_min,
            equipment=equipment,
            restrictions=restrictions,
            user_profile=user_profile,
        )

        # Call LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = self.llm.invoke(messages)
            plan_data = self._parse_response(response.content)
            workout_plan = self._construct_workout_plan(plan_data, weeks, fitness_level, goals, days_per_week, session_duration_min, equipment, restrictions)

            logger.info("Successfully generated workout plan with %d weeks", len(workout_plan.weeks))
            return workout_plan

        except Exception as e:
            logger.error("Workout plan generation failed: %s", e)
            raise

    def _build_system_prompt(self) -> str:
        """Build system prompt with exercise science principles and JSON schema."""
        return """You are a certified personal trainer and exercise scientist creating structured workout plans.

## Your Role
You create evidence-based workout plans following progressive overload, periodization, and appropriate volume/intensity for each fitness level.

## Exercise Science Principles

### Progressive Overload
- Gradually increase volume (sets × reps), intensity (weight), or frequency
- Beginners: Focus on form and neural adaptation
- Intermediates: Add volume and variety
- Advanced: Periodization and intensity techniques

### Volume Landmarks (sets per muscle group per week)
- Beginner: 10-15 sets
- Intermediate: 15-20 sets
- Advanced: 20-25 sets

### Rep Ranges by Goal
- Strength: 3-6 reps (85-95% 1RM)
- Hypertrophy: 8-12 reps (65-85% 1RM)
- Endurance: 15+ reps (40-65% 1RM)
- Mixed: Vary rep ranges throughout week

### Rest Periods
- Strength: 3-5 minutes
- Hypertrophy: 60-90 seconds
- Endurance: 30-60 seconds
- Compound exercises: Longer rest than isolation

### Workout Splits by Frequency
- 3 days/week: Full Body or Upper/Lower/Full
- 4 days/week: Upper/Lower split
- 5-6 days/week: Push/Pull/Legs or Body Part Split

## Safety Guidelines

### Beginner
- Focus on compound movements with bodyweight/light weights
- Emphasize form over weight
- Include deload weeks (reduce volume by 30-40% every 4 weeks)
- Avoid advanced techniques (dropsets, supersets)

### Intermediate
- Introduce progressive overload systematically
- Include variety in exercises and rep ranges
- Can use intensity techniques sparingly

### Advanced
- Periodization with mesocycles
- Advanced techniques (cluster sets, rest-pause, etc.)
- High volume with planned deloads

## JSON Output Schema

You MUST respond with ONLY a valid JSON object (no markdown formatting) with this exact structure:

{
  "weeks": [
    [
      {
        "day_name": "Day 1: Push",
        "focus": "Upper Body Push (Chest, Shoulders, Triceps)",
        "warmup_notes": ["5 min light cardio", "Dynamic stretches - arm circles, shoulder dislocations"],
        "cooldown_notes": ["Static stretches - chest, shoulders", "Foam roll upper back"],
        "exercises": [
          {
            "name": "Barbell Bench Press",
            "description": "Compound chest press movement",
            "sets": 4,
            "reps": "8-10",
            "rest_seconds": 90,
            "tempo": "3-0-1-0",
            "notes": ["Keep feet planted", "Touch chest lightly", "Drive through heels"],
            "equipment": ["barbell", "bench"],
            "muscle_groups": ["chest", "triceps", "front deltoids"]
          }
        ]
      }
    ]
  ]
}

## Critical Requirements
1. Match workout split to days_per_week (e.g., 4 days = Upper/Lower split)
2. Balance muscle groups throughout the week (push/pull balance)
3. Include appropriate rest days (at least 1 per week)
4. Use only equipment from the available list
5. Work around restrictions by substituting exercises
6. Match rep ranges to goals
7. Target the session_duration_min (±10 minutes acceptable)
8. Include 3-6 exercises per session (scale by duration)
9. All equipment names must match available equipment
10. Warmup and cooldown notes must be specific and actionable

Respond with ONLY the JSON object, no additional text."""

    def _build_user_prompt(
        self,
        weeks: int,
        fitness_level: str,
        goals: list[str],
        days_per_week: int,
        session_duration_min: int,
        equipment: list[str],
        restrictions: list[str],
        user_profile: dict | None,
    ) -> str:
        """Build user prompt with specific workout parameters."""
        prompt_lines = [
            f"Create a {weeks}-week workout plan with the following specifications:",
            f"",
            f"**Fitness Level:** {fitness_level}",
            f"**Goals:** {', '.join(goals)}",
            f"**Frequency:** {days_per_week} days per week",
            f"**Session Duration:** {session_duration_min} minutes per session",
            f"**Available Equipment:** {', '.join(equipment) if equipment else 'Bodyweight only'}",
        ]

        if restrictions:
            prompt_lines.append(f"**Restrictions/Injuries:** {', '.join(restrictions)}")
            prompt_lines.append(f"  - Substitute exercises to work around these limitations")
            prompt_lines.append(f"  - Provide alternative movements that avoid the affected areas")

        if user_profile:
            prompt_lines.append(f"")
            prompt_lines.append(f"**User Context:**")
            if "age" in user_profile:
                prompt_lines.append(f"  - Age: {user_profile['age']}")
            if "weight_kg" in user_profile:
                prompt_lines.append(f"  - Weight: {user_profile['weight_kg']} kg")
            if "fitness_goals" in user_profile:
                prompt_lines.append(f"  - Long-term goals: {', '.join(user_profile['fitness_goals'])}")

        prompt_lines.extend([
            f"",
            f"Generate a complete {weeks}-week plan with {days_per_week} workout sessions per week.",
            f"Each week should be a progressive adaptation of the previous week (increase volume or intensity slightly).",
            f"Return ONLY the JSON object following the exact schema provided in the system prompt.",
        ])

        return "\n".join(prompt_lines)

    def _parse_response(self, response_content: str) -> dict[str, Any]:
        """Parse LLM response and extract JSON.

        Handles markdown code blocks like meal planner.
        """
        # Strip markdown code blocks if present
        content = response_content.strip()

        # Remove markdown JSON formatting
        if content.startswith("```json"):
            content = content[7:]  # Remove ```json
        elif content.startswith("```"):
            content = content[3:]  # Remove ```

        if content.endswith("```"):
            content = content[:-3]  # Remove closing ```

        content = content.strip()

        try:
            plan_data = json.loads(content)
            return plan_data
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response as JSON: %s", e)
            logger.debug("Response content: %s", content[:500])
            raise ValueError(f"Invalid JSON response from LLM: {e}")

    def _construct_workout_plan(
        self,
        plan_data: dict[str, Any],
        weeks: int,
        fitness_level: str,
        goals: list[str],
        days_per_week: int,
        session_duration_min: int,
        equipment: list[str],
        restrictions: list[str],
    ) -> WorkoutPlan:
        """Construct WorkoutPlan dataclass from parsed JSON."""
        weeks_list = []

        for week_data in plan_data["weeks"]:
            sessions = []
            for session_data in week_data:
                exercises = []
                for ex_data in session_data["exercises"]:
                    exercise = Exercise(
                        name=ex_data["name"],
                        description=ex_data["description"],
                        sets=ex_data["sets"],
                        reps=ex_data["reps"],
                        rest_seconds=ex_data["rest_seconds"],
                        tempo=ex_data.get("tempo"),  # Optional
                        notes=ex_data["notes"],
                        equipment=ex_data["equipment"],
                        muscle_groups=ex_data["muscle_groups"],
                    )
                    exercises.append(exercise)

                session = WorkoutSession(
                    day_name=session_data["day_name"],
                    focus=session_data["focus"],
                    exercises=exercises,
                    warmup_notes=session_data["warmup_notes"],
                    cooldown_notes=session_data["cooldown_notes"],
                )
                sessions.append(session)

            weeks_list.append(sessions)

        return WorkoutPlan(
            weeks=weeks_list,
            fitness_level=fitness_level,
            goals=goals,
            days_per_week=days_per_week,
            session_duration_min=session_duration_min,
            equipment=equipment,
            restrictions=restrictions,
        )
