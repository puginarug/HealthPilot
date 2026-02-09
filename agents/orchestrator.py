"""LangGraph orchestrator for the multi-agent health assistant.

Coordinates routing between nutrition, exercise, and wellbeing agents
based on user intent classification.
"""

from __future__ import annotations

import logging
import operator
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from agents.exercise_agent import exercise_node
from agents.nutrition_agent import nutrition_node
from agents.wellbeing_agent import wellbeing_node
from config import get_settings
from llm_factory import create_chat_llm
from mcp_servers.registry import get_all_tools

logger = logging.getLogger(__name__)

# Get all tools from MCP registry for centralized tool management
ALL_TOOLS = get_all_tools()
logger.info("Loaded %d tools from MCP registry", len(ALL_TOOLS))


class AgentState(TypedDict):
    """State that flows through the LangGraph orchestrator.

    The `messages` field uses operator.add as a reducer, so each node
    APPENDS messages rather than replacing the list.
    """

    messages: Annotated[list[BaseMessage], operator.add]
    current_agent: str | None
    user_intent: str
    turn_count: int
    error: str | None


ROUTER_SYSTEM_PROMPT = """You are an intent classifier for HealthPilot, a multi-agent health assistant.

Given a user message, classify the PRIMARY intent into exactly ONE category:
- **nutrition**: Food, diet, nutrients, meal planning, calories, vitamins, dietary advice
- **exercise**: Physical activity, workouts, steps, heart rate, fitness, cardio, strength training
- **wellbeing**: Sleep, stress, schedule, work-life balance, rest, recovery, mental health, time management

Respond with ONLY the category name in lowercase, nothing else.

Examples:
- "What foods are high in iron?" → nutrition
- "How many steps did I take this week?" → exercise
- "I'm feeling stressed about my schedule" → wellbeing
- "Can you suggest a post-workout meal?" → nutrition
- "Analyze my sleep patterns" → wellbeing
- "What's my resting heart rate?" → exercise
- "Plan a 7-day meal plan" → nutrition
- "I want to improve my cardio fitness" → exercise
- "How can I sleep better?" → wellbeing
"""


def router_node(state: AgentState) -> dict[str, Any]:
    """Classify user intent and route to the appropriate agent.

    Uses a lightweight LLM call with temperature=0 for deterministic classification.

    Args:
        state: Current agent state.

    Returns:
        State update with classified intent and incremented turn count.
    """
    settings = get_settings()

    if not settings.has_llm_key():
        logger.error("LLM API key not configured")
        return {
            "user_intent": "wellbeing",  # Default fallback
            "current_agent": "router",
            "turn_count": state.get("turn_count", 0) + 1,
            "error": f"{settings.llm_provider.upper()} API key not configured",
        }

    # Extract last user message
    last_user_msg = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break

    if not last_user_msg:
        logger.warning("No user message found in state")
        return {
            "user_intent": "wellbeing",
            "current_agent": "router",
            "turn_count": state.get("turn_count", 0) + 1,
        }

    # Classify intent
    try:
        llm = create_chat_llm(temperature=0.0, max_tokens=20)

        response = llm.invoke([
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(content=last_user_msg),
        ])

        intent = response.content.strip().lower()

        # Validate intent
        valid_intents = {"nutrition", "exercise", "wellbeing"}
        if intent not in valid_intents:
            logger.warning("Invalid intent '%s', defaulting to wellbeing", intent)
            intent = "wellbeing"

        logger.info("Router classified intent: %s for message: %s...", intent, last_user_msg[:50])

        return {
            "user_intent": intent,
            "current_agent": "router",
            "turn_count": state.get("turn_count", 0) + 1,
        }

    except Exception as e:
        logger.error("Router error: %s", e)
        return {
            "user_intent": "wellbeing",
            "current_agent": "router",
            "turn_count": state.get("turn_count", 0) + 1,
            "error": str(e),
        }


def route_to_agent(state: AgentState) -> Literal["nutrition", "exercise", "wellbeing"]:
    """Determine which agent to route to based on classified intent.

    Args:
        state: Current agent state with user_intent.

    Returns:
        Agent name to route to.
    """
    intent = state.get("user_intent", "").lower()

    if intent == "nutrition":
        return "nutrition"
    elif intent == "exercise":
        return "exercise"
    else:
        return "wellbeing"


def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """Check if the last message has tool calls that need execution.

    Args:
        state: Current agent state.

    Returns:
        "tools" if tool execution needed, "end" otherwise.
    """
    if not state["messages"]:
        return "end"

    last_message = state["messages"][-1]

    # Check if the last message has tool_calls attribute (AIMessage from Claude)
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.info("Tool calls detected: %d tools", len(last_message.tool_calls))
        return "tools"

    return "end"


def route_after_tools(state: AgentState) -> Literal["nutrition", "exercise", "wellbeing"]:
    """Route back to the agent that invoked the tools.

    Args:
        state: Current agent state.

    Returns:
        Agent name to return to.
    """
    current = state.get("current_agent", "wellbeing")
    if current in ("nutrition", "exercise", "wellbeing"):
        return current
    return "wellbeing"  # Safe fallback


def build_graph() -> StateGraph:
    """Build and compile the HealthPilot orchestrator graph.

    Returns:
        Compiled LangGraph StateGraph ready for invocation.
    """
    # Initialize graph with AgentState schema
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("nutrition", nutrition_node)
    graph.add_node("exercise", exercise_node)
    graph.add_node("wellbeing", wellbeing_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))

    # Entry point: always start with router
    graph.add_edge(START, "router")

    # Router -> conditional routing to agents based on intent
    graph.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "nutrition": "nutrition",
            "exercise": "exercise",
            "wellbeing": "wellbeing",
        },
    )

    # Each agent -> check if tools need to be called
    for agent_name in ["nutrition", "exercise", "wellbeing"]:
        graph.add_conditional_edges(
            agent_name,
            should_continue,
            {
                "tools": "tools",
                "end": END,
            },
        )

    # After tool execution -> route back to the agent that called them
    graph.add_conditional_edges(
        "tools",
        route_after_tools,
        {
            "nutrition": "nutrition",
            "exercise": "exercise",
            "wellbeing": "wellbeing",
        },
    )

    logger.info("Compiled HealthPilot orchestrator graph")
    return graph.compile()
