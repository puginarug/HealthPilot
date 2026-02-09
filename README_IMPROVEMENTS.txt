## Improvements Summary

✅ **Flexible LLM Provider Support**
- Switch between Anthropic Claude or OpenAI GPT
- Use gpt-4o-mini for 15x cost savings (/usr/bin/bash.30/month vs .50/month for 1000 messages)
- Configure via LLM_PROVIDER and LLM_MODEL in .env
- See llm_factory.py and IMPROVEMENTS.md for details

✅ **MCP Tool Organization**
- Tools organized into categorized MCP servers (nutrition, health-data, wellness)
- Centralized registry in mcp_servers/registry.py
- Better tool management and reusability
- Easy to extend with new tool servers

## Quick Configuration

Choose your LLM provider in .env:

Option 1 (Budget-friendly):
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...

Option 2 (Maximum quality):
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514
ANTHROPIC_API_KEY=sk-ant-...

See IMPROVEMENTS.md for cost comparison, migration guide, and detailed documentation.

