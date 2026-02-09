# HealthPilot Architecture

## System Overview

HealthPilot uses a multi-agent architecture where specialized agents (Nutrition, Exercise, Wellbeing) are coordinated by a LangGraph orchestrator. The system demonstrates modern ML engineering patterns: RAG, agent orchestration, and data analytics.

## Component Architecture

### 1. Agent Layer (LangGraph)

**Orchestrator** (`agents/orchestrator.py`):
- Intent classification using Claude (temperature=0 for deterministic routing)
- Conditional routing via `StateGraph`
- Tool execution via `ToolNode`
- State management with `AgentState` TypedDict

**State Flow**:
```
START → Router → [Nutrition|Exercise|Wellbeing] → Tools? → Agent → END
```

**AgentState Schema**:
```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    current_agent: str | None
    user_intent: str
    turn_count: int
    error: str | None
```

### 2. Agent Implementations

Each agent follows the same pattern:
1. System prompt defining role and capabilities
2. Tools bound to Claude via `bind_tools()`
3. Node function that takes state, invokes LLM, returns updated state

**Nutrition Agent**:
- Tools: `search_nutrition_knowledge`, `lookup_food_nutrients`, `search_dietary_research`
- Data sources: USDA FoodData Central, PubMed abstracts
- Emphasizes evidence-based advice with source citations

**Exercise Agent**:
- Tools: `analyze_activity_data`, `analyze_heart_rate_data`, `get_exercise_recommendations`
- Data sources: Wearable CSV exports (daily_activity.csv, heart_rate.csv)
- Provides data-driven workout guidance

**Wellbeing Agent**:
- Tools: `analyze_sleep_data`, `suggest_wellness_activities`
- Data sources: Sleep CSV export (sleep.csv)
- Focuses on rest, recovery, schedule balance

### 3. RAG Pipeline

**Vector Store** (ChromaDB):
- Persistent local storage (`data/chroma_db/`)
- Two collections: `nutrition_docs`, `pubmed_abstracts`
- OpenAI text-embedding-3-small (1536 dims, $0.02/1M tokens)

**Document Sources**:
- **USDA**: FoodData Central API → ~1000 foods with full nutrient profiles
- **PubMed**: E-utilities API → ~500 research abstracts on nutrition/exercise topics

**Retrieval** (`rag/retriever.py`):
```python
retriever.retrieve(query, collections=["nutrition_docs", "pubmed_abstracts"], top_k=5)
```
- Multi-collection search with score-based reranking
- Deduplication by content prefix
- Source attribution in formatted context

### 4. Analytics Pipeline

**Data Loading** (`analytics/data_pipeline.py`):
- CSV parsing with pandas
- Date/time normalization
- Column validation

**Metrics Computation** (`analytics/health_metrics.py`):
- Rolling averages (7-day, 30-day)
- Trend detection via `scipy.stats.linregress`
- Anomaly detection (Z-score based)
- Summary dataclasses: `ActivitySummary`, `SleepSummary`, `HeartRateSummary`

**Visualizations** (`analytics/visualizations.py`):
- Plotly chart generators
- Consistent theming via `apply_theme()`
- Charts: steps timeline, sleep patterns, HR zones, correlations

**Insights** (`analytics/insights.py`):
- Rule-based insight generation
- Evidence-based thresholds (WHO activity guidelines, NSF sleep recommendations)
- Severity levels: info, positive, warning, alert

### 5. Frontend (Streamlit)

**Multi-page app** with `st.navigation()`:
- **Chat**: LangGraph orchestrator interface with agent routing transparency
- **Dashboard**: Interactive analytics with date range filtering
- **Meal Plan / Schedule / RAG Explorer**: Placeholder pages for future features

**State Management**:
- Session state for chat history (`st.session_state.chat_messages`)
- Cached data loading (`@st.cache_data`) for performance
- Compiled graph cached in session (`st.session_state.agent_graph`)

## Data Flow

### Chat Request Flow

```
User input (Chat page)
    ↓
Orchestrator.router_node()
    ↓ (Claude API call for intent classification)
Intent: "nutrition"
    ↓
nutrition_node(state)
    ↓ (Claude API call with tools)
AIMessage with tool_calls: [search_nutrition_knowledge("iron sources")]
    ↓
ToolNode executes tool
    ↓ (ChromaDB semantic search)
ToolMessage with results
    ↓
nutrition_node(state) again
    ↓ (Claude API call with tool results)
Final AIMessage with answer
    ↓
Displayed to user
```

### Analytics Data Flow

```
CSV files (data/sample/*.csv)
    ↓
HealthDataLoader.load_*()
    ↓ (pandas parsing & validation)
DataFrame
    ↓
HealthMetrics.compute_*_summary()
    ↓ (scipy/numpy computations)
SummaryDataclass
    ↓
InsightEngine.analyze_*()
    ↓
list[Insight]
    ↓
Rendered in Dashboard (Streamlit)
```

## Key Design Decisions

### 1. Flat vs Nested LangGraph
**Choice**: Flat graph with 3 agents
**Rationale**: Nested sub-graphs add complexity without benefit at this scale. Clear LangSmith traces matter more for debugging.

### 2. LLM-based Router
**Choice**: Claude-based intent classification (not keyword/regex)
**Rationale**: Flexible, handles natural language variations. Temperature=0 ensures determinism. Cost is ~50 tokens/query.

### 3. OpenAI Embeddings
**Choice**: text-embedding-3-small ($0.02/1M tokens)
**Rationale**: Cheaper and simpler than managing local ONNX models. Acceptable API dependency for RAG use case.

### 4. ChromaDB Local Storage
**Choice**: PersistentClient (file-based)
**Rationale**: ~15K document chunks fit comfortably in local storage. Avoids separate database process.

### 5. Tool-based Agents
**Choice**: LangChain tools via `@tool` decorator
**Rationale**: Claude's native tool calling provides structured function invocation. ToolNode handles execution automatically.

## Scalability Considerations

**Current limitations**:
- Single-user (no auth or multi-tenancy)
- In-memory session state (Streamlit)
- Local ChromaDB (not horizontally scalable)

**How to scale**:
1. **Multi-user**: Add PostgreSQL for user data + LangGraph checkpoints
2. **Distributed vector store**: Migrate ChromaDB → Pinecone/Weaviate
3. **Async agents**: Use `astream` for non-blocking LLM calls
4. **Caching**: Redis for LLM response caching

## Testing Strategy

**Unit tests** (`tests/test_*.py`):
- Analytics: Pure functions, no mocks needed
- RAG: Mock ChromaDB and embeddings
- Agents: Mock Claude API calls

**Integration tests**:
- End-to-end orchestrator flow with real tools
- Agent routing logic

**Test coverage target**: 80%+ on core logic (analytics, RAG, agents)

## Observability

**LangSmith Integration**:
- All LLM calls traced automatically
- Custom `run_name` tags on each node
- Trace URL: https://smith.langchain.com/
- Project name: `healthpilot`

**Logging**:
- Python stdlib `logging` (not print)
- Format: `%(asctime)s | %(name)s | %(levelname)s | %(message)s`
- Module-level loggers: `logger = logging.getLogger(__name__)`

## Security Considerations

- **Secrets**: All API keys in SecretStr (pydantic-settings)
- **Input validation**: Pandas validates CSV columns
- **SQL injection**: N/A (no SQL database)
- **XSS**: Streamlit handles HTML escaping
- **Rate limiting**: Retry logic with tenacity (exponential backoff)

## Future Architecture Enhancements

1. **Google Calendar Integration**: OAuth2 flow + real-time event sync
2. **Streaming responses**: Use LangGraph's `astream()` for token-by-token UI updates
3. **Agent memory**: Add `SqliteSaver` checkpoints for conversation persistence
4. **Multi-modal input**: Image-based food logging via Claude vision
5. **Batch processing**: Async document ingestion for faster RAG population
