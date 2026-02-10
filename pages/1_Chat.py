"""AI Chat page - conversational interface to the multi-agent orchestrator.

Routes user messages to specialized agents (nutrition, exercise, wellbeing)
and displays responses with source attribution.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agents.orchestrator import build_graph
from config import get_settings
from integrations.google_calendar import GoogleCalendarClient

logger = logging.getLogger(__name__)


def extract_citations(messages: list) -> list[dict]:
    """Extract citations from ToolMessage objects.

    Looks for patterns from web search results:
    - [Source N: Title]
      URL: https://...
      Relevance: 0.95

    Args:
        messages: List of message objects from orchestrator.

    Returns:
        List of citation dictionaries with source type and metadata.
    """
    citations = []

    for msg in messages:
        if not isinstance(msg, ToolMessage):
            continue

        content = str(msg.content)

        # Extract web search citations (new format from Tavily)
        # Pattern: [Source N: Title]\nURL: https://...\nRelevance: 0.XX
        source_pattern = r'\[Source \d+:\s*([^\]]+)\]\s*\n\s*URL:\s*(https?://[^\s]+)\s*\n\s*Relevance:\s*([\d.]+)'
        for match in re.finditer(source_pattern, content):
            title = match.group(1).strip()
            url = match.group(2).strip()
            relevance = float(match.group(3))

            # Determine source type from URL
            if "pubmed.ncbi.nlm.nih.gov" in url or "pmc.ncbi.nlm.nih.gov" in url:
                source_type = "pubmed"
            elif "usda.gov" in url or "fdc.nal.usda.gov" in url:
                source_type = "usda"
            elif "nih.gov" in url:
                source_type = "nih"
            elif "cdc.gov" in url:
                source_type = "cdc"
            elif ".edu" in url:
                source_type = "academic"
            else:
                source_type = "other"

            citations.append({
                "source": source_type,
                "title": title,
                "url": url,
                "relevance": relevance
            })

        # Also extract URLs that appear inline in AI responses (fallback)
        # Pattern: According to [Source Name] (URL)
        inline_pattern = r'According to ([^(]+)\s*\((https?://[^)]+)\)'
        for match in re.finditer(inline_pattern, content):
            source_name = match.group(1).strip()
            url = match.group(2).strip()

            citations.append({
                "source": "inline",
                "title": source_name,
                "url": url,
                "relevance": None
            })

    # Remove duplicates based on URL
    seen = set()
    unique_citations = []
    for cite in citations:
        url = cite.get("url")
        if url and url not in seen:
            seen.add(url)
            unique_citations.append(cite)

    return unique_citations


def extract_wellness_suggestions(response_text: str) -> list[dict]:
    """Extract wellness activity suggestions from AI response.

    Looks for patterns like:
    - "1. Activity name (duration)"
    - "Deep breathing exercises (5 min)"
    - Numbered lists with activities

    Args:
        response_text: AI response content.

    Returns:
        List of suggestion dictionaries with title and duration.
    """
    suggestions = []

    # Pattern: numbered activity with optional duration
    # Examples: "1. Deep breathing (5 min)", "2. Nature walk"
    pattern = r'(?:^|\n)\s*\d+\.\s*([^(\n]+?)(?:\s*\(([^)]+)\))?(?:\n|$)'

    # Check if response contains wellness-related keywords
    wellness_keywords = ["wellness", "stress", "activity", "activities", "suggestion", "meditation", "breathing", "walk", "journal"]
    has_wellness_content = any(kw in response_text.lower() for kw in wellness_keywords)

    if has_wellness_content:
        for match in re.finditer(pattern, response_text):
            title = match.group(1).strip()
            duration = match.group(2).strip() if match.group(2) else "15 min"

            # Filter out very short or irrelevant matches
            if len(title) > 5 and not title.lower().startswith("remember"):
                suggestions.append({
                    "title": title,
                    "duration": duration,
                    "category": _categorize_activity(title),
                })

    return suggestions[:5]  # Limit to 5 suggestions


def _categorize_activity(title: str) -> str:
    """Categorize activity type for icon selection."""
    title_lower = title.lower()

    if any(word in title_lower for word in ["call", "social", "friend", "family", "talk"]):
        return "social"
    elif any(word in title_lower for word in ["walk", "exercise", "yoga", "workout", "hike"]):
        return "movement"
    elif any(word in title_lower for word in ["breathing", "meditation", "mindfulness", "relax"]):
        return "mindfulness"
    elif any(word in title_lower for word in ["journal", "write", "plan", "gratitude"]):
        return "reflection"
    else:
        return "general"


def add_to_calendar(activity_title: str, duration_str: str) -> tuple[bool, str]:
    """Add wellness activity to Google Calendar.

    Args:
        activity_title: Title of the activity.
        duration_str: Duration string (e.g., "15 min", "30 minutes").

    Returns:
        Tuple of (success: bool, message: str).
    """
    try:
        # Parse duration
        duration_match = re.search(r'(\d+)', duration_str)
        duration_minutes = int(duration_match.group(1)) if duration_match else 15

        # Create calendar client
        calendar_client = GoogleCalendarClient()

        # Schedule for tomorrow at 9 AM (configurable)
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        start_iso = start_time.strftime("%Y-%m-%dT%H:%M:%S")

        # Create event
        event = calendar_client.create_event(
            title=f"Wellness Activity: {activity_title}",
            start_time=start_iso,
            duration_minutes=duration_minutes,
            description=f"Wellness activity suggested by HealthPilot.\n\nActivity: {activity_title}\nDuration: {duration_str}",
        )

        if event:
            event_link = event.get("htmlLink", "")
            return True, f"Added to calendar for {start_time.strftime('%B %d at %I:%M %p')}"
        else:
            return False, "Failed to create calendar event."

    except FileNotFoundError:
        return False, "Google Calendar not configured. Set up credentials first."
    except Exception as e:
        logger.error("Calendar creation failed: %s", e)
        return False, f"Error: {str(e)}"


def send_email_reminder(activity_title: str, duration_str: str) -> tuple[bool, str]:
    """Send email reminder for wellness activity.

    Args:
        activity_title: Title of the activity.
        duration_str: Duration string.

    Returns:
        Tuple of (success: bool, message: str).
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        settings = get_settings()

        # Get email configuration from environment
        smtp_host = settings.env_vars.get("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(settings.env_vars.get("SMTP_PORT", "587"))
        smtp_username = settings.env_vars.get("SMTP_USERNAME")
        smtp_password = settings.env_vars.get("SMTP_PASSWORD")
        user_email = settings.env_vars.get("USER_EMAIL")

        if not all([smtp_username, smtp_password, user_email]):
            return False, "Email not configured. Add SMTP settings to .env file."

        # Create message
        msg = MIMEMultipart()
        msg["From"] = smtp_username
        msg["To"] = user_email
        msg["Subject"] = f"Wellness Reminder: {activity_title}"

        body = f"""
Hi {settings.env_vars.get('USER_NAME', 'there')}!

This is a reminder to take care of your wellbeing with this activity:

**{activity_title}**
Duration: {duration_str}

Suggested by your HealthPilot assistant.

Take a moment for yourself - you deserve it!

---
HealthPilot AI Health Assistant
        """

        msg.attach(MIMEText(body, "plain"))

        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        logger.info("Email reminder sent for: %s", activity_title)
        return True, f"Email reminder sent to {user_email}"

    except Exception as e:
        logger.error("Email send failed: %s", e)
        return False, f"Email failed: {str(e)}"


st.header("AI Chat")

# Check API key and show which provider is being used
settings = get_settings()
provider_display = "Claude" if settings.llm_provider == "anthropic" else "OpenAI GPT"
st.caption(f"Powered by {provider_display} + LangGraph multi-agent system")
if not settings.has_llm_key():
    st.error(f"LLM API key not configured (current provider: {settings.llm_provider})")

    st.markdown("### 🔑 Configure Your LLM Provider")
    st.markdown("HealthPilot supports **Anthropic Claude** or **OpenAI GPT** models.")

    tab1, tab2 = st.tabs(["🤖 Use OpenAI (Recommended for Cost)", "🔮 Use Anthropic Claude"])

    with tab1:
        st.markdown("**OpenAI GPT** - Fast and affordable")
        st.code("""LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...""", language="bash")
        st.caption("Cost: ~$0.15 per 1M input tokens")

    with tab2:
        st.markdown("**Anthropic Claude** - Most capable reasoning")
        st.code("""LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514
ANTHROPIC_API_KEY=sk-ant-...""", language="bash")
        st.caption("Cost: ~$3 per 1M input tokens")

    st.divider()
    st.info("💡 Add these to your `.env` file (local) or **Streamlit Cloud Secrets** (deployed)")
    st.stop()

# Initialize session state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
    # Add welcome message
    welcome = AIMessage(content=(
        "Hi! I'm HealthPilot, your AI health assistant.\n\n"
        "I provide evidence-based guidance on **nutrition, exercise, and wellbeing** "
        "using real-time web search of credible academic sources (USDA, NIH, PubMed, CDC, .edu institutions).\n\n"
        "What would you like to know?"
    ))
    st.session_state.chat_messages.append(welcome)

if "agent_graph" not in st.session_state:
    with st.spinner("Initializing agents..."):
        try:
            st.session_state.agent_graph = build_graph()
            logger.info("Agent graph built successfully")
        except Exception as e:
            st.error(f"Failed to initialize agents: {e}")
            st.stop()

# Display chat history
for msg in st.session_state.chat_messages:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.markdown(msg.content)

# Chat input
if user_input := st.chat_input("Ask about nutrition, exercise, or wellbeing..."):
    # Add user message
    user_msg = HumanMessage(content=user_input)
    st.session_state.chat_messages.append(user_msg)

    with st.chat_message("user"):
        st.markdown(user_input)

    # Invoke orchestrator
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Prepare initial state
                initial_state = {
                    "messages": st.session_state.chat_messages,
                    "current_agent": None,
                    "user_intent": "",
                    "turn_count": 0,
                    "error": None,
                }

                # Invoke graph
                result = st.session_state.agent_graph.invoke(initial_state)

                # Extract final AI message(s)
                new_messages = result["messages"][len(st.session_state.chat_messages):]
                ai_messages = [m for m in new_messages if isinstance(m, AIMessage)]

                if ai_messages:
                    final_response = ai_messages[-1]
                    st.markdown(final_response.content)

                    # Extract and display citations
                    citations = extract_citations(new_messages)
                    if citations:
                        with st.expander("📚 Sources & Citations", expanded=False):
                            for i, cite in enumerate(citations, 1):
                                source_type = cite["source"]

                                # Icon mapping for source types
                                source_icons = {
                                    "pubmed": "🔬",
                                    "usda": "🌾",
                                    "nih": "🏛️",
                                    "cdc": "🏥",
                                    "academic": "🎓",
                                    "other": "📄",
                                    "inline": "🔗"
                                }
                                icon = source_icons.get(source_type, "📄")

                                # Source name mapping
                                source_names = {
                                    "pubmed": "PubMed Research",
                                    "usda": "USDA Nutrition Database",
                                    "nih": "NIH - National Institutes of Health",
                                    "cdc": "CDC - Centers for Disease Control",
                                    "academic": "Academic Institution",
                                    "other": "Academic Source",
                                    "inline": "Reference"
                                }
                                source_name = source_names.get(source_type, "Source")

                                # Display citation
                                st.markdown(f"{icon} **{i}. {source_name}**")
                                st.markdown(f"[{cite['title']}]({cite['url']})")

                                if cite.get("relevance"):
                                    st.caption(f"Relevance: {cite['relevance']:.2f}")

                                if i < len(citations):
                                    st.divider()

                    # Extract and display wellness suggestions
                    wellness_suggestions = extract_wellness_suggestions(final_response.content)
                    if wellness_suggestions:
                        st.markdown("---")
                        st.subheader("💡 Suggested Wellness Activities")
                        st.caption("Take action on these suggestions to improve your wellbeing")

                        # Display suggestions in columns (max 3 per row)
                        for i in range(0, len(wellness_suggestions), 3):
                            cols = st.columns(min(3, len(wellness_suggestions) - i))

                            for col, suggestion in zip(cols, wellness_suggestions[i:i+3]):
                                with col:
                                    # Choose icon based on category
                                    icons = {
                                        "social": "👥",
                                        "movement": "🚶",
                                        "mindfulness": "🧘",
                                        "reflection": "📝",
                                        "general": "✨",
                                    }
                                    icon = icons.get(suggestion["category"], "✨")

                                    st.info(f"{icon} **{suggestion['title']}**\n\n⏱️ {suggestion['duration']}")

                                    # Action buttons
                                    col1, col2 = st.columns(2)

                                    with col1:
                                        if st.button(
                                            "📅 Calendar",
                                            key=f"cal_{suggestion['title']}_{i}",
                                            help="Add to Google Calendar",
                                            use_container_width=True,
                                        ):
                                            success, message = add_to_calendar(
                                                suggestion["title"],
                                                suggestion["duration"]
                                            )
                                            if success:
                                                st.success(message, icon="✅")
                                            else:
                                                st.error(message, icon="❌")

                                    with col2:
                                        if st.button(
                                            "✉️ Email",
                                            key=f"email_{suggestion['title']}_{i}",
                                            help="Send email reminder",
                                            use_container_width=True,
                                        ):
                                            success, message = send_email_reminder(
                                                suggestion["title"],
                                                suggestion["duration"]
                                            )
                                            if success:
                                                st.success(message, icon="✅")
                                            else:
                                                st.error(message, icon="❌")

                    # Update session state with ALL new messages (including tool messages)
                    st.session_state.chat_messages.extend(new_messages)

                    # Show routing info in expander
                    with st.expander("🔧 Agent Details", expanded=False):
                        st.write(f"**Intent:** {result.get('user_intent', 'N/A')}")
                        st.write(f"**Handled by:** {result.get('current_agent', 'N/A')} agent")
                        st.write(f"**Turn count:** {result.get('turn_count', 0)}")

                        if result.get("error"):
                            st.error(f"Error: {result['error']}")

                        # Show tool calls if any
                        tool_calls_made = any(
                            hasattr(m, "tool_calls") and m.tool_calls
                            for m in new_messages if isinstance(m, AIMessage)
                        )
                        if tool_calls_made:
                            st.info(f"This response used {len([m for m in new_messages if isinstance(m, ToolMessage)])} data retrieval tool(s)")

                else:
                    st.warning("No response received from agents.")

            except Exception as e:
                logger.exception("Chat invocation failed")
                st.error(f"An error occurred: {e}")
                st.info("Make sure all API keys are configured in your .env file.")

# Sidebar: additional info
with st.sidebar:
    st.divider()
    st.subheader("Chat Features")

    st.write("**Nutrition Agent**")
    st.caption("USDA food data, PubMed research, meal planning")

    st.write("**Exercise Agent**")
    st.caption("Activity analysis, heart rate insights, workout plans")

    st.write("**Wellbeing Agent**")
    st.caption("Sleep analysis, schedule balance, wellness tips")

    if st.button("Clear Chat History"):
        st.session_state.chat_messages = []
        st.rerun()

    # Show LangSmith link if enabled
    if settings.has_langsmith():
        st.divider()
        st.caption(f"LangSmith tracing active")
        st.caption(f"Project: {settings.langchain_project}")
