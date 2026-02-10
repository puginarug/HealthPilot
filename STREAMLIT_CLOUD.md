# 🚀 Deploy HealthPilot to Streamlit Cloud

This guide will help you deploy HealthPilot as a public Streamlit app in ~10 minutes.

## Prerequisites
- GitHub account
- API keys (Anthropic Claude, OpenAI)
- Streamlit Cloud account (free at https://share.streamlit.io)

## Step-by-Step Deployment

### 1. Push to GitHub

If you haven't already created a GitHub repository:

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - HealthPilot multi-agent health assistant"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/HealthPilot.git
git branch -M main
git push -u origin main
```

**Important**: Make sure `.env` is in `.gitignore` (it already is - don't commit API keys!)

### 2. Deploy on Streamlit Cloud

1. **Go to Streamlit Cloud**: https://share.streamlit.io
2. **Sign in** with your GitHub account
3. **Click "New app"**
4. **Configure deployment**:
   - Repository: `YOUR_USERNAME/HealthPilot`
   - Branch: `main`
   - Main file path: `streamlit_app.py`
   - App URL: Choose your custom subdomain (e.g., `healthpilot-demo.streamlit.app`)

### 3. Configure Secrets (API Keys)

Before the app starts, configure your API keys:

1. In Streamlit Cloud dashboard, click on your app
2. Go to **Settings** → **Secrets**
3. Add your secrets in TOML format:

**Option A: Use OpenAI (Recommended - Cheaper)**
```toml
# LLM Provider
LLM_PROVIDER = "openai"
LLM_MODEL = "gpt-4o-mini"

# Required: OpenAI API (for chat AND embeddings)
OPENAI_API_KEY = "sk-your-openai-key-here"

# Optional: LangSmith for debugging (recommended)
LANGCHAIN_TRACING_V2 = "true"
LANGSMITH_API_KEY = "lsv2_your_langsmith_key"
LANGCHAIN_PROJECT = "healthpilot"
```

**Option B: Use Anthropic Claude**
```toml
# LLM Provider
LLM_PROVIDER = "anthropic"
LLM_MODEL = "claude-sonnet-4-20250514"

# Required: Claude API (for chat)
ANTHROPIC_API_KEY = "sk-ant-your-key-here"

# Required: OpenAI API (for embeddings only)
OPENAI_API_KEY = "sk-your-openai-key-here"

# Optional: LangSmith for debugging (recommended)
LANGCHAIN_TRACING_V2 = "true"
LANGSMITH_API_KEY = "lsv2_your_langsmith_key"
LANGCHAIN_PROJECT = "healthpilot"
```

4. **Click "Save"**

### 4. Deploy!

Click **"Deploy"** and wait 2-3 minutes for the app to build and start.

Your app will be live at: `https://your-subdomain.streamlit.app`

## 🎉 What Works Out of the Box

✅ **Multi-agent chat** with Nutrition, Exercise, and Wellbeing agents
✅ **RAG citations** from USDA FoodData and PubMed research (pre-populated database included)
✅ **Meal planner** with shopping lists
✅ **Workout planner** with calendar export
✅ **Health analytics dashboard** with sample data
✅ **User profile management**

## ⚠️ Important Limitations

### 1. **No Data Persistence**
- Streamlit Cloud uses **ephemeral storage** (resets on every restart)
- User profiles saved via the Profile page **will be lost** on app restart
- Uploaded CSV health data **will not persist**
- Workaround: Download your profile/data regularly, or use the app for testing only

### 2. **Pre-Populated Data**
- ChromaDB vector store (36MB) is committed to the repo and will work immediately
- Sample health data (90 days) is included in `data/sample/`
- Users can upload their own data, but it won't persist

### 3. **Google Calendar Integration**
- Requires OAuth2 setup with Google Cloud Console
- Not included by default (users need to set up their own credentials)
- See `docs/DEPLOYMENT.md` for setup instructions

## 🔧 Customization Tips

### Change App Theme
Edit `.streamlit/config.toml` and update theme colors:
```toml
[theme]
primaryColor = "#your-color"
backgroundColor = "#your-color"
```

### Adjust Python Version
Create `.python-version` file:
```
3.12
```

### Add Analytics
Enable Streamlit Cloud analytics in Settings → Analytics

## 📊 Cost Estimates

**Free Tier Usage** (for demo/portfolio):
- Streamlit Cloud: **Free** (1 public app)
- OpenAI GPT-4o-mini: **Free tier** (limited usage)
- OpenAI Embeddings: **~$0.02 total** (ChromaDB pre-populated)
- Total: **$0/month** (within free tiers)

**Public Usage** (100 users, 1,000 messages/month):

**Option A: OpenAI GPT-4o-mini** (Recommended for cost)
- LLM (GPT-4o-mini): **~$0.15/month** (1M input tokens = 1,000 messages)
- Embeddings: **~$0** (already embedded)
- Streamlit Cloud: **Free**
- **Total: ~$0.15/month** 💰

**Option B: Anthropic Claude Sonnet**
- LLM (Claude Sonnet 4.5): **~$3/month** (1M input tokens)
- Embeddings: **~$0** (already embedded)
- Streamlit Cloud: **Free**
- **Total: ~$3/month**

## 🐛 Troubleshooting

### App won't start
- **Check logs**: Dashboard → Manage app → Logs
- **Common issue**: Missing secrets (API keys not configured)
- **Solution**: Add secrets in Settings → Secrets

### "ChromaDB collection not found"
- **Cause**: ChromaDB not included in repo
- **Solution**: Ensure `data/chroma_db/` is NOT in `.gitignore` and is committed

### "Anthropic API key not configured"
- **Cause**: Secrets not set correctly
- **Solution**: Check Settings → Secrets has `ANTHROPIC_API_KEY`

### Import errors
- **Cause**: Missing dependencies
- **Solution**: Ensure `requirements.txt` is committed and up to date

### Slow first load
- **Expected**: First load takes ~1 minute to install dependencies
- **Subsequent loads**: Much faster (~10 seconds)

## 📱 Share Your App

Once deployed, share your app URL:
```
https://your-subdomain.streamlit.app
```

Add it to your:
- GitHub README
- Portfolio website
- LinkedIn profile
- Resume

## 🔒 Security Best Practices

✅ **Never commit** `.env` file (already in `.gitignore`)
✅ **Use Streamlit secrets** for all API keys
✅ **Enable XSRF protection** (already enabled in config)
✅ **Limit upload size** (configured to 50MB)
✅ **Monitor API usage** to prevent unexpected costs

## 🚀 Next Steps

1. **Test your deployment**: Try all features (chat, meal planner, workout planner)
2. **Add Google Calendar OAuth** (optional, see `docs/DEPLOYMENT.md`)
3. **Customize branding**: Update theme colors and app title
4. **Monitor costs**: Check Anthropic and OpenAI dashboards weekly
5. **Add to portfolio**: Share the link and source code

## 📚 Additional Resources

- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [Full Deployment Guide](docs/DEPLOYMENT.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Anthropic API Docs](https://docs.anthropic.com/)
