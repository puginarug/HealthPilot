# Agent Design Documentation

## Overview

HealthPilot uses three specialized agents (Nutrition, Exercise, Wellbeing) coordinated by a LangGraph orchestrator. Each agent has custom tools, carefully crafted prompts, and follows evidence-based guidelines.

## Nutrition Agent

**File**: `agents/nutrition_agent.py`

**Purpose**: Provide evidence-based dietary guidance backed by USDA and PubMed data.

**Tools**:
- `search_nutrition_knowledge`: Search USDA + PubMed
- `lookup_food_nutrients`: Get specific food nutrition data
- `search_dietary_research`: Query PubMed research
- `get_user_profile`: Read dietary preferences

**Key Guidelines**:
- Always cite sources (USDA FDC IDs, PubMed PMIDs)
- Use metric units (grams, kcal, mg)
- Ground advice in data (use tools before making claims)
- Distinguish information from medical advice

## Exercise Agent

**File**: `agents/exercise_agent.py`

**Purpose**: Analyze activity data and provide personalized workout guidance.

**Tools**:
- `analyze_activity_data`: Analyze steps, trends, patterns
- `analyze_heart_rate_data`: HR zones, resting HR analysis
- `get_exercise_recommendations`: Evidence-based workout plans
- `read_google_calendar` / `create_calendar_event`: Schedule workouts (placeholders)

**Key Guidelines**:
- Data-driven recommendations (analyze actual user data first)
- Progressive approach (gradual increases)
- Clear HR zone targets
- Safety emphasis (warmup, recovery, listen to body)

## Wellbeing Agent

**File**: `agents/wellbeing_agent.py`

**Purpose**: Optimize sleep and work-life balance. NOT a therapist.

**Tools**:
- `analyze_sleep_data`: Sleep quality and consistency metrics
- `analyze_schedule_balance`: Work/life ratios (placeholder)
- `suggest_wellness_activities`: Practical stress relief activities

**Key Guidelines**:
- Evidence-based sleep science (NSF recommendations)
- TIME management focus (not emotional counseling)
- Practical, achievable suggestions
- Refer to professionals for mental health concerns

**Sleep Guidelines**:
- 7-9 hours for adults (NSF)
- Consistent bedtime ±30 min
- Social jet lag (weekend shift >1h) impairs performance

## Router

**File**: `agents/orchestrator.py`

**Purpose**: Classify user intent and route to appropriate agent.

**Classification**:
- **nutrition**: Food, diet, nutrients, meal planning
- **exercise**: Activity, workouts, fitness, heart rate
- **wellbeing**: Sleep, stress, schedule, work-life balance

Uses Claude with temperature=0 and max_tokens=20 for fast, deterministic classification.

## Adding New Agents

To add a new agent:

1. Create `agents/new_agent.py` following the pattern
2. Define tools with clear docstrings
3. Write comprehensive system prompt
4. Create node function returning state update
5. Update orchestrator routing logic
6. Add to `ALL_TOOLS` list
7. Update router prompt with new intent category

## Tool Development

**Best Practices**:
- Detailed docstrings (Claude reads them)
- Error handling (graceful failures)
- Return strings (not complex objects)
- Log errors with Python logging

**Example Tool**:
```python
@tool
def analyze_activity_data(period_days: int = 30) -> str:
    '''Analyze activity data for a given period.

    Args:
        period_days: Number of recent days to analyze.

    Returns:
        Activity summary with steps, trends, recommendations.
    '''
    try:
        # Load and process data
        return formatted_results
    except FileNotFoundError:
        return "Data not found. Ensure CSV exists."
```

## Prompt Engineering

**Structure**:
1. **Role definition**: "You are the X Agent..."
2. **Capabilities**: List what it can do
3. **Guidelines**: How to behave, what to avoid
4. **Examples**: Show expected interactions
5. **Stay-in-scope**: When to defer to other agents

## Testing

**Unit Tests**: Mock LLM calls, test tool invocation
**Integration Tests**: Test full orchestrator routing
**End-to-End**: Test with real API calls (optional)

## Performance

- Cache LLM responses for repeated queries
- Use streaming for long responses
- Enable parallel tool calls
- Monitor with LangSmith

For detailed implementation examples, see the agent source files in `agents/`.
