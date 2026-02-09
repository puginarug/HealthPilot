"""Exercise library with reference data for form cues and muscle groups.

Pre-populated library of common exercises with detailed information for safe execution.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExerciseReference:
    """Reference information for an exercise."""

    name: str
    category: str  # "compound" | "isolation" | "cardio" | "flexibility"
    primary_muscles: list[str]
    secondary_muscles: list[str]
    equipment: list[str]
    difficulty: str  # "beginner" | "intermediate" | "advanced"
    form_cues: list[str]
    common_mistakes: list[str]
    variations: list[str]


# Pre-populated exercise library
EXERCISE_LIBRARY = {
    # === CHEST EXERCISES ===
    "Barbell Bench Press": ExerciseReference(
        name="Barbell Bench Press",
        category="compound",
        primary_muscles=["chest"],
        secondary_muscles=["triceps", "front deltoids"],
        equipment=["barbell", "bench"],
        difficulty="intermediate",
        form_cues=[
            "Feet planted flat on floor",
            "Shoulder blades retracted and pinned to bench",
            "Lower bar to mid-chest with control",
            "Touch chest lightly, don't bounce",
            "Press bar up and slightly back toward face",
            "Drive through legs and maintain arch",
        ],
        common_mistakes=[
            "Bouncing bar off chest",
            "Flaring elbows too wide (>45°)",
            "Lifting butt off bench",
            "Uneven bar path",
        ],
        variations=[
            "Dumbbell Bench Press",
            "Incline Barbell Bench Press",
            "Close-Grip Bench Press",
            "Floor Press",
        ],
    ),
    "Push-Ups": ExerciseReference(
        name="Push-Ups",
        category="compound",
        primary_muscles=["chest"],
        secondary_muscles=["triceps", "front deltoids", "core"],
        equipment=["bodyweight"],
        difficulty="beginner",
        form_cues=[
            "Hands slightly wider than shoulder-width",
            "Body in straight line from head to heels",
            "Core engaged throughout",
            "Lower chest to 1-2 inches from floor",
            "Elbows at 45° angle to body",
            "Push through entire palm, not just fingers",
        ],
        common_mistakes=[
            "Sagging hips",
            "Neck hyperextension (looking up)",
            "Flaring elbows too wide",
            "Incomplete range of motion",
        ],
        variations=[
            "Incline Push-Ups (easier)",
            "Decline Push-Ups (harder)",
            "Diamond Push-Ups (triceps focus)",
            "Wide Push-Ups (chest focus)",
        ],
    ),
    "Dumbbell Flyes": ExerciseReference(
        name="Dumbbell Flyes",
        category="isolation",
        primary_muscles=["chest"],
        secondary_muscles=["front deltoids"],
        equipment=["dumbbells", "bench"],
        difficulty="intermediate",
        form_cues=[
            "Slight bend in elbows throughout movement",
            "Lower dumbbells out to sides in arc motion",
            "Feel stretch in chest at bottom",
            "Bring dumbbells together over chest",
            "Maintain same elbow angle (don't bend/straighten)",
        ],
        common_mistakes=[
            "Straightening/bending elbows (becomes press)",
            "Going too heavy",
            "Hyperextending shoulders at bottom",
        ],
        variations=[
            "Incline Dumbbell Flyes",
            "Cable Flyes",
            "Pec Deck",
        ],
    ),
    # === BACK EXERCISES ===
    "Barbell Deadlift": ExerciseReference(
        name="Barbell Deadlift",
        category="compound",
        primary_muscles=["lower back", "glutes", "hamstrings"],
        secondary_muscles=["traps", "lats", "core", "forearms"],
        equipment=["barbell"],
        difficulty="advanced",
        form_cues=[
            "Feet hip-width apart, bar over mid-foot",
            "Grip bar just outside shins",
            "Chest up, shoulders over bar",
            "Brace core before pulling",
            "Drive through heels, extend hips and knees simultaneously",
            "Keep bar close to body throughout",
            "Finish with hips forward, shoulders back",
        ],
        common_mistakes=[
            "Rounding lower back",
            "Bar drifting away from body",
            "Hyperextending back at top",
            "Jerking bar off floor",
        ],
        variations=[
            "Romanian Deadlift",
            "Sumo Deadlift",
            "Trap Bar Deadlift",
            "Single-Leg Deadlift",
        ],
    ),
    "Pull-Ups": ExerciseReference(
        name="Pull-Ups",
        category="compound",
        primary_muscles=["lats"],
        secondary_muscles=["biceps", "rhomboids", "core"],
        equipment=["pull-up bar"],
        difficulty="intermediate",
        form_cues=[
            "Grip bar slightly wider than shoulder-width",
            "Hang with arms fully extended",
            "Pull shoulder blades down and back first",
            "Lead with chest, not chin",
            "Pull until chin over bar",
            "Lower with control to full extension",
        ],
        common_mistakes=[
            "Kipping or swinging",
            "Incomplete range of motion",
            "Shrugging shoulders at top",
            "Not engaging lats at start",
        ],
        variations=[
            "Chin-Ups (underhand grip)",
            "Neutral-Grip Pull-Ups",
            "Assisted Pull-Ups",
            "Weighted Pull-Ups",
        ],
    ),
    "Barbell Row": ExerciseReference(
        name="Barbell Row",
        category="compound",
        primary_muscles=["lats", "rhomboids"],
        secondary_muscles=["biceps", "lower back", "traps"],
        equipment=["barbell"],
        difficulty="intermediate",
        form_cues=[
            "Hip hinge to 45° torso angle",
            "Grip bar shoulder-width apart",
            "Pull bar to lower chest/upper abdomen",
            "Lead with elbows, not hands",
            "Squeeze shoulder blades at top",
            "Maintain neutral spine throughout",
        ],
        common_mistakes=[
            "Using too much body english",
            "Rounding back",
            "Pulling to wrong position (chest vs. belly)",
            "Not keeping core braced",
        ],
        variations=[
            "Pendlay Row",
            "Yates Row (underhand grip)",
            "Dumbbell Row",
            "T-Bar Row",
        ],
    ),
    # === LEG EXERCISES ===
    "Barbell Squat": ExerciseReference(
        name="Barbell Squat",
        category="compound",
        primary_muscles=["quadriceps", "glutes"],
        secondary_muscles=["hamstrings", "core", "lower back"],
        equipment=["barbell", "squat rack"],
        difficulty="intermediate",
        form_cues=[
            "Bar on upper traps (high bar) or rear delts (low bar)",
            "Feet shoulder-width apart, toes slightly out",
            "Chest up, core braced",
            "Break at hips and knees simultaneously",
            "Descend until thighs parallel to ground (or lower)",
            "Knees track over toes",
            "Drive through heels to stand",
        ],
        common_mistakes=[
            "Knees caving inward",
            "Excessive forward lean",
            "Rising onto toes",
            "Incomplete depth",
            "Not bracing core",
        ],
        variations=[
            "Front Squat",
            "Goblet Squat",
            "Bulgarian Split Squat",
            "Box Squat",
        ],
    ),
    "Romanian Deadlift": ExerciseReference(
        name="Romanian Deadlift",
        category="compound",
        primary_muscles=["hamstrings", "glutes"],
        secondary_muscles=["lower back", "lats"],
        equipment=["barbell"],
        difficulty="intermediate",
        form_cues=[
            "Start standing with bar at hip level",
            "Slight bend in knees throughout",
            "Push hips back while maintaining neutral spine",
            "Lower bar down shins until hamstring stretch",
            "Keep bar close to legs",
            "Drive hips forward to return to standing",
        ],
        common_mistakes=[
            "Rounding lower back",
            "Bending knees too much (becomes squat)",
            "Bar drifting away from body",
            "Not feeling hamstring stretch",
        ],
        variations=[
            "Single-Leg Romanian Deadlift",
            "Dumbbell RDL",
            "Stiff-Leg Deadlift",
        ],
    ),
    "Lunges": ExerciseReference(
        name="Lunges",
        category="compound",
        primary_muscles=["quadriceps", "glutes"],
        secondary_muscles=["hamstrings", "core"],
        equipment=["bodyweight", "dumbbells"],
        difficulty="beginner",
        form_cues=[
            "Step forward with long stride",
            "Lower back knee toward floor",
            "Front shin should be vertical",
            "Torso upright",
            "Push through front heel to return",
            "Maintain balance throughout",
        ],
        common_mistakes=[
            "Knee extending past toes",
            "Leaning forward",
            "Short stride length",
            "Back knee touching floor hard",
        ],
        variations=[
            "Reverse Lunges",
            "Walking Lunges",
            "Bulgarian Split Squats",
            "Jumping Lunges",
        ],
    ),
    # === SHOULDER EXERCISES ===
    "Overhead Press": ExerciseReference(
        name="Overhead Press",
        category="compound",
        primary_muscles=["front deltoids", "side deltoids"],
        secondary_muscles=["triceps", "traps", "core"],
        equipment=["barbell"],
        difficulty="intermediate",
        form_cues=[
            "Bar rests on front deltoids at collarbone",
            "Grip slightly wider than shoulder-width",
            "Elbows slightly in front of bar",
            "Brace core and glutes",
            "Press bar straight up, moving head back slightly",
            "Lock out overhead with biceps by ears",
            "Lower with control to start position",
        ],
        common_mistakes=[
            "Excessive back arch",
            "Not moving head back (bar path interrupted)",
            "Pressing bar forward instead of straight up",
            "Not locking out overhead",
        ],
        variations=[
            "Dumbbell Shoulder Press",
            "Push Press",
            "Arnold Press",
            "Seated Overhead Press",
        ],
    ),
    "Lateral Raises": ExerciseReference(
        name="Lateral Raises",
        category="isolation",
        primary_muscles=["side deltoids"],
        secondary_muscles=[],
        equipment=["dumbbells"],
        difficulty="beginner",
        form_cues=[
            "Slight forward lean",
            "Slight bend in elbows",
            "Raise dumbbells out to sides",
            "Lead with elbows, not hands",
            "Stop at shoulder height",
            "Lower with control",
        ],
        common_mistakes=[
            "Using momentum/swinging",
            "Shrugging shoulders",
            "Raising too high (traps take over)",
            "Going too heavy",
        ],
        variations=[
            "Cable Lateral Raises",
            "Bent-Over Lateral Raises",
            "Front Raises",
        ],
    ),
    # === ARM EXERCISES ===
    "Barbell Curl": ExerciseReference(
        name="Barbell Curl",
        category="isolation",
        primary_muscles=["biceps"],
        secondary_muscles=["forearms"],
        equipment=["barbell"],
        difficulty="beginner",
        form_cues=[
            "Stand with feet hip-width apart",
            "Grip bar shoulder-width, underhand",
            "Elbows tight to sides",
            "Curl bar up, keeping elbows stationary",
            "Squeeze biceps at top",
            "Lower with control",
        ],
        common_mistakes=[
            "Swinging body for momentum",
            "Elbows moving forward",
            "Not controlling descent",
            "Incomplete range of motion",
        ],
        variations=[
            "Dumbbell Curls",
            "Hammer Curls",
            "Preacher Curls",
            "Cable Curls",
        ],
    ),
    "Tricep Dips": ExerciseReference(
        name="Tricep Dips",
        category="compound",
        primary_muscles=["triceps"],
        secondary_muscles=["chest", "front deltoids"],
        equipment=["dip bars", "bodyweight"],
        difficulty="intermediate",
        form_cues=[
            "Grip bars with straight arms",
            "Lean forward slightly for chest, upright for triceps",
            "Lower body by bending elbows",
            "Go to 90° elbow bend",
            "Push through palms to return",
            "Keep shoulders down (don't shrug)",
        ],
        common_mistakes=[
            "Going too deep (shoulder strain)",
            "Shrugging shoulders",
            "Flaring elbows out",
            "Using momentum",
        ],
        variations=[
            "Bench Dips",
            "Weighted Dips",
            "Assisted Dips",
        ],
    ),
    # === CORE EXERCISES ===
    "Plank": ExerciseReference(
        name="Plank",
        category="isolation",
        primary_muscles=["core"],
        secondary_muscles=["shoulders"],
        equipment=["bodyweight"],
        difficulty="beginner",
        form_cues=[
            "Forearms on floor, elbows under shoulders",
            "Body in straight line from head to heels",
            "Engage core, squeeze glutes",
            "Neutral neck (look down)",
            "Breathe normally",
            "Hold position",
        ],
        common_mistakes=[
            "Sagging hips",
            "Raised hips (pyramid shape)",
            "Looking up (neck strain)",
            "Holding breath",
        ],
        variations=[
            "Side Plank",
            "Plank with Shoulder Taps",
            "RKC Plank (max tension)",
        ],
    ),
    "Hanging Leg Raises": ExerciseReference(
        name="Hanging Leg Raises",
        category="isolation",
        primary_muscles=["core", "hip flexors"],
        secondary_muscles=["lats"],
        equipment=["pull-up bar"],
        difficulty="advanced",
        form_cues=[
            "Hang from bar with straight arms",
            "Engage lats to stabilize shoulders",
            "Raise legs up, keeping them straight or slightly bent",
            "Lift until hips flex past 90°",
            "Lower with control",
            "Avoid swinging",
        ],
        common_mistakes=[
            "Swinging body",
            "Using momentum",
            "Not lifting high enough",
            "Relaxing shoulders",
        ],
        variations=[
            "Knee Raises (easier)",
            "Toes to Bar",
            "L-Sit Hold",
        ],
    ),
}


def get_exercise_reference(name: str) -> ExerciseReference | None:
    """Get reference information for an exercise by name.

    Args:
        name: Exercise name to look up

    Returns:
        ExerciseReference if found, None otherwise
    """
    return EXERCISE_LIBRARY.get(name)


def search_exercises(
    equipment: list[str] | None = None,
    muscle_group: str | None = None,
    difficulty: str | None = None,
    category: str | None = None,
) -> list[ExerciseReference]:
    """Search exercise library by filters.

    Args:
        equipment: Filter by required equipment
        muscle_group: Filter by targeted muscle group
        difficulty: Filter by difficulty level
        category: Filter by exercise category

    Returns:
        List of matching ExerciseReference objects
    """
    results = list(EXERCISE_LIBRARY.values())

    if equipment:
        # Match if any of the user's equipment is in the exercise's equipment list
        results = [ex for ex in results if any(eq in ex.equipment for eq in equipment)]

    if muscle_group:
        # Match if muscle_group is in primary or secondary muscles
        results = [
            ex
            for ex in results
            if muscle_group.lower() in [m.lower() for m in ex.primary_muscles + ex.secondary_muscles]
        ]

    if difficulty:
        results = [ex for ex in results if ex.difficulty == difficulty.lower()]

    if category:
        results = [ex for ex in results if ex.category == category.lower()]

    return results


def get_all_muscle_groups() -> list[str]:
    """Get list of all unique muscle groups in the library.

    Returns:
        Sorted list of muscle group names
    """
    muscle_groups = set()
    for ex in EXERCISE_LIBRARY.values():
        muscle_groups.update(ex.primary_muscles)
        muscle_groups.update(ex.secondary_muscles)
    return sorted(list(muscle_groups))


def get_all_equipment() -> list[str]:
    """Get list of all unique equipment types in the library.

    Returns:
        Sorted list of equipment names
    """
    equipment_types = set()
    for ex in EXERCISE_LIBRARY.values():
        equipment_types.update(ex.equipment)
    return sorted(list(equipment_types))
