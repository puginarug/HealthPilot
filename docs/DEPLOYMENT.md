# Deployment Guide

## Local Development Setup

### Prerequisites
- Python 3.11-3.13
- [uv](https://docs.astral.sh/uv/) package manager
- API keys (see below)

### Step-by-Step Setup

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone repository and install dependencies**:
   ```bash
   cd HealthPilot
   uv sync
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and configure your LLM provider:

   **Option A: OpenAI (Recommended for cost)**
   ```env
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4o-mini
   OPENAI_API_KEY=sk-...              # Required for chat AND embeddings
   LANGCHAIN_TRACING_V2=true          # Optional: LangSmith
   LANGSMITH_API_KEY=lsv2_...         # Optional: LangSmith
   ```

   **Option B: Anthropic Claude**
   ```env
   LLM_PROVIDER=anthropic
   LLM_MODEL=claude-sonnet-4-20250514
   ANTHROPIC_API_KEY=sk-ant-...       # Required for agents
   OPENAI_API_KEY=sk-...              # Required for embeddings only
   LANGCHAIN_TRACING_V2=true          # Optional: LangSmith
   LANGSMITH_API_KEY=lsv2_...         # Optional: LangSmith
   ```

4. **Generate sample data**:
   ```bash
   uv run python data/generate_sample_data.py
   ```

5. **Populate RAG knowledge base**:
   ```bash
   uv run python -m rag.ingest --source usda --limit 1000
   uv run python -m rag.ingest --source pubmed --limit 100
   ```

6. **Run the application**:
   ```bash
   uv run streamlit run streamlit_app.py
   ```

7. **Access**: http://localhost:8501

## API Key Setup

### 1. Anthropic Claude API (Required)
- Sign up: https://console.anthropic.com/
- Create API key: https://console.anthropic.com/settings/keys
- Free tier: $5 credit
- Cost: ~$0.003 per message (Claude Sonnet 3.5)

### 2. OpenAI API (Required for RAG)
- Sign up: https://platform.openai.com/signup
- Create API key: https://platform.openai.com/api-keys
- Cost: $0.02 per 1M tokens for embeddings
- Embedding ~1000 USDA foods costs ~$0.10

### 3. LangSmith (Optional but Recommended)
- Sign up: https://smith.langchain.com/
- Create API key in settings
- Free tier: 5K traces/month
- Benefits: Debug agent flows, view LLM calls, inspect tool execution

### 4. USDA FoodData Central (Optional)
- Sign up: https://fdc.nal.usda.gov/api-key-signup.html
- Free, no credit card required
- Without key: uses DEMO_KEY (rate limited to 30 req/hour)

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | No | anthropic | LLM provider: "anthropic" or "openai" |
| `LLM_MODEL` | No | claude-sonnet-4-20250514 | Model name (e.g., gpt-4o-mini, claude-sonnet-4-20250514) |
| `LLM_MAX_TOKENS` | No | 4096 | Max tokens per response |
| `LLM_TEMPERATURE` | No | 0.3 | Creativity (0.0-1.0) |
| `ANTHROPIC_API_KEY` | If using Claude | - | Anthropic API key |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key (for chat if LLM_PROVIDER=openai, always needed for embeddings) |
| `OPENAI_EMBEDDING_MODEL` | No | text-embedding-3-small | Embedding model |
| `CHROMA_PERSIST_DIRECTORY` | No | ./data/chroma_db | ChromaDB storage path |
| `LANGCHAIN_TRACING_V2` | No | false | Enable LangSmith tracing |
| `LANGSMITH_API_KEY` | If using LangSmith | - | LangSmith API key (replaces deprecated LANGCHAIN_API_KEY) |
| `LANGCHAIN_PROJECT` | No | healthpilot | LangSmith project name |
| `USDA_API_KEY` | No | DEMO_KEY | USDA API key |
| `LOG_LEVEL` | No | INFO | Logging level |

## Streamlit Cloud Deployment

### Prerequisites
- GitHub repository
- Streamlit Cloud account (free)
- API keys configured as secrets

### Steps

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/healthpilot.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**:
   - Go to https://share.streamlit.io/
   - Click "New app"
   - Select your GitHub repo
   - Main file: `streamlit_app.py`
   - Python version: 3.12

3. **Configure Secrets**:
   - In Streamlit Cloud dashboard → Settings → Secrets
   - Add your configuration (TOML format):

   **Using OpenAI (cheaper):**
   ```toml
   LLM_PROVIDER = "openai"
   LLM_MODEL = "gpt-4o-mini"
   OPENAI_API_KEY = "sk-..."
   LANGCHAIN_TRACING_V2 = "true"
   LANGSMITH_API_KEY = "lsv2_..."
   ```

   **Using Anthropic Claude:**
   ```toml
   LLM_PROVIDER = "anthropic"
   LLM_MODEL = "claude-sonnet-4-20250514"
   ANTHROPIC_API_KEY = "sk-ant-..."
   OPENAI_API_KEY = "sk-..."  # Still needed for embeddings
   LANGCHAIN_TRACING_V2 = "true"
   LANGSMITH_API_KEY = "lsv2_..."
   ```

4. **Generate data on first run**:
   - Add a startup script or run manually via SSH

### Limitations
- ChromaDB must be rebuilt on each deploy (ephemeral filesystem)
- Consider moving to cloud vector store (Pinecone, Weaviate) for production

## Docker Deployment (Future)

Dockerfile template:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml .python-version ./
COPY . .

# Install dependencies
RUN uv sync --no-dev

# Generate data
RUN uv run python data/generate_sample_data.py

# Expose Streamlit port
EXPOSE 8501

# Run app
CMD ["uv", "run", "streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0"]
```

## Troubleshooting

### Issue: "Anthropic API key not configured"
**Solution**: Check `.env` file has `ANTHROPIC_API_KEY=sk-ant-...`

### Issue: "No results found" in RAG search
**Solution**: Run `python -m rag.ingest --source all` to populate ChromaDB

### Issue: "Activity data not found"
**Solution**: Run `python data/generate_sample_data.py` to create sample CSVs

### Issue: Import errors
**Solution**: Run `uv sync` to ensure all dependencies are installed

### Issue: ChromaDB "collection not found"
**Solution**: Delete `data/chroma_db/` and re-run ingestion

## Performance Optimization

### 1. Cache LLM Responses
Add Redis or LangChain caching:
```python
from langchain.cache import RedisCache
langchain.llm_cache = RedisCache()
```

### 2. Async Agent Calls
Use `astream()` for non-blocking responses:
```python
async for event in graph.astream(state):
    # Process streaming events
```

### 3. Batch Embeddings
Embed documents in larger batches (100-500 at a time)

### 4. Optimize ChromaDB
- Use HNSW index for faster search
- Increase `batch_size` during ingestion
- Enable query caching

## Security Checklist

- [ ] All API keys in `.env` (not committed to git)
- [ ] `.gitignore` includes `.env` and sensitive files
- [ ] Streamlit Cloud secrets configured (not in repo)
- [ ] Rate limiting configured for public deployments
- [ ] Input validation on user messages
- [ ] HTTPS enabled (Streamlit Cloud does this automatically)

## Monitoring & Observability

### LangSmith Setup
1. Sign up at https://smith.langchain.com/
2. Create a project named `healthpilot`
3. Add API key to `.env`:
   ```env
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=lsv2_...
   LANGCHAIN_PROJECT=healthpilot
   ```
4. View traces: https://smith.langchain.com/

### Logs
Application logs to stdout in format:
```
2026-02-08 10:30:15 | agents.orchestrator | INFO | Router classified intent: nutrition
```

View logs in Streamlit Cloud: Dashboard → Logs

## Cost Estimates

**Monthly costs for moderate usage** (100 users, 10 messages/user/month):

| Service | Usage | Cost |
|---------|-------|------|
| Claude API | 1000 messages × 1000 tokens | ~$3.00 |
| OpenAI Embeddings | 100K tokens | ~$0.002 |
| LangSmith | 1000 traces | Free tier |
| Streamlit Cloud | Hosting | Free tier |
| **Total** | | **~$3/month** |

For production scale (10K+ users), consider:
- Claude: ~$300-500/month
- Vector DB (Pinecone): ~$70/month
- Compute: ~$100/month
