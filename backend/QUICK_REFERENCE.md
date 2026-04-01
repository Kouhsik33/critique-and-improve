# Quick Reference Card

## System Overview

Multi-agent AI system with 5 specialized agents orchestrated by LangGraph for iterative idea refinement through structured feedback loops.

## Quick Start (30 seconds)

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Add OPENAI_API_KEY=...

# 3. Start services
docker-compose up &

# 4. Run backend
uvicorn app.main:app --reload

# 5. Test
curl http://localhost:8000/health
```

## Core API (5 Main Endpoints)

```bash
# Start workflow
curl -X POST http://localhost:8000/run \
  -d '{"prompt": "Your idea", "max_iterations": 5}'

# Check status
curl http://localhost:8000/status/{request_id}

# Get metrics
curl http://localhost:8000/metrics/{request_id}

# Stream live events
wscat -c ws://localhost:8000/stream/{request_id}

# Search ideas
curl -X POST http://localhost:8000/ideas/{workflow_id}/search \
  -d '{"query": "search term"}'
```

## Agent Capabilities

| Agent | Role | Temperature | Output |
|-------|------|-------------|--------|
| **Creator** | Generate ideas | 0.8 | Novel solutions |
| **Critic** | Find flaws | 0.5 | Issues & severity |
| **Radical** | Challenge assumptions | 0.9 | Paradigm shifts |
| **Synthesizer** | Integrate feedback | 0.6 | Refined ideas |
| **Judge** | Evaluate quality | 0.3 | Accept/Iterate |

## Workflow Loop

```
Creator → Critic → Radical → Synthesizer → Judge
                                              ↓
                                    [Fitness ≥ 0.55?]
                                    ↙              ↘
                                 YES              NO
                                  ↓                ↓
                               DONE            (Loop)
```

## Key Metrics

```
Idea:     Novelty | Feasibility | Clarity | Impact | Fitness
Agent:    Tokens | Quality | Confidence
System:   Iterations | Convergence | Conflict | Efficiency
```

## Configuration

```bash
# Custom models per agent
{
  "model_mapping": {
    "creator": "gpt-4-turbo",
    "critic": "gpt-4-turbo",
    "radical": "gpt-4",
    "synthesizer": "gpt-3.5-turbo",
    "judge": "gpt-4"
  }
}

# Temperature (0.0-1.0)
creator_temperature=0.8      # Creative
critic_temperature=0.5       # Balanced
judge_temperature=0.3        # Deterministic
```

## File Structure

```
app/
├── main.py                 ← FastAPI app
├── config/llm_config.py   ← LLM factory
├── agents/                ← 5 agent modules
├── graph/workflow.py      ← LangGraph orchestration
├── memory/                ← Vector store + state
├── metrics/metrics_engine.py ← Metrics calculation
├── streaming/             ← Redis + WebSocket
├── schemas/               ← Pydantic models
├── services/              ← Execution orchestration
└── db/postgres.py         ← Database
```

## Environment Variables (.env)

```env
# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_agents

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Health Checks

```bash
# Service health
curl http://localhost:8000/health

# Dependencies
curl http://localhost:8000/health/dependencies

# Configuration
curl http://localhost:8000/debug/config
```

## Docker Deployment

```bash
# One command deploy
docker-compose up

# Or manual
docker build -t ai-agents-backend .
docker run -p 8000:8000 ai-agents-backend
```

## Performance Targets

- Response time: <100ms per agent
- Throughput: 10+ concurrent workflows
- Token efficiency: >1000 tokens per iteration
- Convergence: <5 iterations typical

## Supported LLM Models

| Provider | Models |
|----------|--------|
| OpenAI | gpt-4, gpt-4-turbo, gpt-3.5-turbo |
| Anthropic | claude-3-opus, claude-3-sonnet, claude-2 |
| Google | gemini-pro |

## Database Schema

```
workflow_logs        → Execution history
agent_metrics        → Per-agent performance
idea_metrics         → Per-idea quality
system_metrics       → System-level stats
```

## Real-Time Events

```javascript
// Agent Action
{
  type: "agent_action",
  agent: "creator|critic|radical|synthesizer|judge",
  action: "generate|attack|disrupt|merge|judge",
  data: {...}
}

// Workflow Complete
{
  type: "workflow_complete",
  data: {
    final_output: "...",
    total_iterations: 3,
    metrics: {...}
  }
}
```

## Metrics Acceptance Criteria

For workflow to complete:
- Novelty ≥ 0.6
- Feasibility ≥ 0.5
- Clarity ≥ 0.6
- Impact ≥ 0.5
- Fitness ≥ 0.55

## Common Use Cases

1. **Product Ideation**: Generate and refine product concepts
2. **Problem Solving**: Systematically improve solutions
3. **Strategy Development**: Iterate on business strategies
4. **Research Synthesis**: Combine ideas from multiple sources
5. **Content Creation**: Refine articles, documents, proposals

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Check PostgreSQL/Redis running |
| API key error | Set OPENAI_API_KEY in .env |
| Timeout | Increase max_iterations or reduce temperature |
| High tokens | Use cheaper models or fewer iterations |

## Documentation

- `README.md` - Full user guide
- `API_REFERENCE.md` - Endpoint documentation
- `IMPLEMENTATION_SUMMARY.md` - Technical overview
- `/docs` - Swagger UI
- `/redoc` - ReDoc UI

## Monitoring

```bash
# Watch status
watch -n 2 'curl http://localhost:8000/status/{id}'

# Monitor logs
tail -f logs/backend.log

# Check metrics
curl http://localhost:8000/metrics/{id} | jq
```

## Production Checklist

- [ ] Set real API keys
- [ ] Configure PostgreSQL for persistence
- [ ] Setup Redis properly
- [ ] Enable authentication
- [ ] Configure rate limiting
- [ ] Setup monitoring/logging
- [ ] Backup database regularly
- [ ] Use production ASGI server
- [ ] Setup SSL/HTTPS
- [ ] Configure auto-scaling

## Quick Customization

**Add new agent**: Extend `BaseAgent` in `app/agents/`
**Change workflow**: Edit `WorkflowOrchestrator.graph` in `workflow.py`
**Add metric**: Update `MetricsCalculator` in `metrics_engine.py`
**Customize endpoint**: Add route in `app/main.py`

---

**Version**: 1.0.0 | **Status**: Production Ready | **Support**: See README.md
