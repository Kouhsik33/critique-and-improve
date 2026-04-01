# Multi-Agent AI System - Backend

A production-grade backend for a collaborative multi-agent AI system that simulates intelligent feedback loops and iterative improvement through structured agent orchestration.

## System Architecture

### Core Concept

This system mimics a team of experts working together:

- **Creator** → Generates novel ideas
- **Critic** → Evaluates flaws and weaknesses
- **Radical** → Challenges assumptions and proposes alternatives
- **Synthesizer** → Integrates improvements into refined idea
- **Judge** → Evaluates output quality and decides iteration

The system iterates until optimal output emerges through structured feedback loops.

## Technology Stack

- **Python 3.9+**
- **FastAPI** - Modern async web framework
- **LangGraph** - Workflow orchestration for multi-agent systems
- **LangChain** - LLM abstraction layer (supports OpenAI, Anthropic, Google)
- **Redis** - Real-time pub/sub streaming
- **PostgreSQL** - Persistent metrics and logs
- **FAISS** - Vector similarity search for memory and idea retrieval

## Project Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── config/
│   │   └── llm_config.py         # LLM factory and configuration
│   ├── agents/
│   │   ├── base_agent.py         # Base agent class
│   │   ├── creator.py            # Idea generation agent
│   │   ├── critic.py             # Evaluation agent
│   │   ├── radical.py            # Disruptor agent
│   │   ├── synthesizer.py        # Integration agent
│   │   └── judge.py              # Decision agent
│   ├── graph/
│   │   └── workflow.py           # LangGraph workflow orchestration
│   ├── memory/
│   │   └── vector_store.py       # FAISS-based memory system
│   ├── metrics/
│   │   └── metrics_engine.py     # Metrics tracking and calculation
│   ├── streaming/
│   │   ├── redis_streaming.py    # Redis pub/sub streaming
│   │   └── websocket.py          # WebSocket connection management
│   ├── schemas/
│   │   └── state_schema.py       # Pydantic schemas for data
│   ├── services/
│   │   └── execution_service.py  # Workflow execution orchestration
│   └── db/
│       └── postgres.py           # PostgreSQL integration
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment configuration template
└── README.md                     # Documentation
```

## Installation

### Prerequisites

1. Python 3.9 or higher
2. PostgreSQL 12+
3. Redis 6+
4. OpenAI API key (or Anthropic/Google API keys)

### Setup Steps

1. **Clone the repository**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup PostgreSQL**
   ```sql
   CREATE DATABASE ai_agents;
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and database credentials
   ```

6. **Start Redis**
   ```bash
   redis-server
   ```

7. **Run the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

The API will be available at `http://localhost:8000`

## API Endpoints

### 1. Health Check

```bash
GET /health
```

**Response**: Service health status

### 2. Start Workflow

```bash
POST /run
Content-Type: application/json

{
    "prompt": "Your idea or problem to iterate on",
    "max_iterations": 5,
    "temperature": 0.7,
    "model_mapping": {
        "creator": "gpt-4-turbo",
        "critic": "gpt-4-turbo",
        "radical": "gpt-4",
        "synthesizer": "gpt-3.5-turbo",
        "judge": "gpt-4"
    }
}
```

**Response**: Request ID for tracking workflow execution

```json
{
    "request_id": "run_abc12345",
    "status": "started",
    "message": "Workflow execution started"
}
```

### 3. Real-time Streaming (WebSocket)

```
WS /stream/{request_id}
```

Subscribe to real-time agent events:

```json
{
    "type": "agent_action",
    "agent": "creator",
    "action": "generate",
    "data": {...},
    "iteration": 0,
    "timestamp": "2024-01-01T12:00:00Z"
}
```

**Event Types**:
- `agent_action`: Agent performed an action
- `feedback`: Feedback from judge
- `iteration_complete`: Iteration finished
- `workflow_complete`: Entire workflow finished

### 4. Get Metrics

```bash
GET /metrics/{request_id}
```

**Response**: Detailed metrics for the workflow

```json
{
    "idea_metrics": [
        {
            "novelty": 0.8,
            "feasibility": 0.6,
            "clarity": 0.7,
            "impact": 0.75,
            "fitness_score": 0.7125
        }
    ],
    "agent_metrics": {
        "creator": [
            {
                "token_count": 250,
                "quality_score": 0.75,
                "confidence": 0.65
            }
        ],
        ...
    },
    "system_metrics": {
        "iteration_count": 3,
        "convergence_speed": 0.15,
        "total_token_usage": 3500,
        "conflict_intensity": 0.45,
        "token_efficiency": 1166.67
    }
}
```

### 5. Workflow Status

```bash
GET /status/{request_id}
```

**Response**: Current workflow status

```json
{
    "request_id": "run_abc12345",
    "status": "running|completed|failed",
    "iteration": 2,
    "total_iterations": 5,
    "connected_clients": 3
}
```

### 6. Search Similar Ideas

```bash
POST /ideas/{workflow_id}/search
Content-Type: application/json

{
    "query": "Search query for similar ideas"
}
```

### 7. Evolution History

```bash
GET /evolution/{workflow_id}
```

**Response**: Complete evolution history of ideas

### 8. Dependency Health

```bash
GET /health/dependencies
```

Checks database, Redis, and LLM connectivity.

## Agent Details

### Creator Agent

**Purpose**: Generate novel, creative ideas  
**Key Behaviors**:
- Thinks outside conventional boundaries
- Generates multiple diverse solution angles
- Embraces unconventional approaches
- Temperature: 0.8 (creative)

**Output Structure**:
```json
{
    "ideas": [
        {
            "title": "Brief title",
            "description": "Detailed description",
            "novelty_justification": "Why this is novel",
            "key_innovation": "Core element"
        }
    ],
    "reasoning": "Creative thinking process",
    "diversity": "How ideas differ"
}
```

### Critic Agent

**Purpose**: Identify weaknesses and areas for improvement  
**Evaluates**:
- Technical feasibility
- Resource requirements
- Market viability
- Implementation challenges
- Unintended consequences

**Output Structure**:
```json
{
    "critiques": [
        {
            "idea_index": 0,
            "issues": [
                {
                    "category": "feasibility|clarity|logic|resources|viability",
                    "severity": "low|medium|high",
                    "description": "Issue description",
                    "impact": "How it affects the idea"
                }
            ]
        }
    ]
}
```

### Radical Agent

**Purpose**: Challenge assumptions and propose paradigm shifts  
**Analyzes**:
- Fundamental assumptions
- Inverted assumptions
- Extreme alternatives
- Breakthrough possibilities

### Synthesizer Agent

**Purpose**: Integrate feedback into refined, cohesive solution  
**Incorporates**:
- Legitimate critiques
- Valuable radical suggestions
- Feasibility constraints
- Explicit trade-offs

### Judge Agent

**Purpose**: Evaluate quality and decide on iteration  
**Acceptance Criteria**:
- Novelty ≥ 0.6
- Feasibility ≥ 0.5
- Clarity ≥ 0.6
- Impact ≥ 0.5
- Overall Fitness ≥ 0.55

## Metrics System

### Idea-Level Metrics

- **Novelty** (0-1): Uniqueness compared to history
- **Feasibility** (0-1): Practical viability
- **Clarity** (0-1): Communication quality
- **Impact** (0-1): Potential effect
- **Fitness Score**: Weighted average of above

### Agent-Level Metrics

- **Token Count**: API tokens used
- **Quality Score**: Output quality (0-1)
- **Confidence**: Agent confidence in output
- **Accuracy** (for Critic): Issue detection accuracy
- **Diversity** (for Creator): Solution diversity

### System-Level Metrics

- **Iteration Count**: Number of refinement cycles
- **Convergence Speed**: Rate of improvement
- **Token Usage**: Total API tokens per iteration
- **Conflict Intensity**: Disagreement between agents
- **Token Efficiency**: Tokens per iteration

## Memory System

The vector store (FAISS) remembers:

- **Past Ideas**: All generated ideas for similarity search
- **Critiques**: Identified issues with categorization
- **Evolution**: History of idea improvements
- **Patterns**: Patterns in agent outputs

Access via:
```bash
# Search similar ideas
POST /ideas/{workflow_id}/search

# Get evolution history
GET /evolution/{workflow_id}
```

## Configuration

### LLM Models

Customize models per agent in `.env`:

```env
CREATOR_MODEL=gpt-4-turbo
CRITIC_MODEL=gpt-4-turbo
RADICAL_MODEL=gpt-4
SYNTHESIZER_MODEL=gpt-3.5-turbo
JUDGE_MODEL=gpt-4
```

Or pass `model_mapping` in API request:

```json
{
    "prompt": "...",
    "model_mapping": {
        "creator": "claude-3-opus",
        "critic": "gpt-4-turbo",
        ...
    }
}
```

### Temperature Settings

Control creativity vs determinism (0.0 = deterministic, 1.0 = creative):

```env
CREATOR_TEMPERATURE=0.8      # Creative
CRITIC_TEMPERATURE=0.5       # Balanced
RADICAL_TEMPERATURE=0.9      # Very creative
SYNTHESIZER_TEMPERATURE=0.6  # Balanced
JUDGE_TEMPERATURE=0.3        # Deterministic
```

## Workflow Execution Flow

```
[Creator] 
    ↓ (generates ideas)
[Critic]
    ↓ (identifies issues)
[Radical]
    ↓ (challenges assumptions)
[Synthesizer]
    ↓ (integrates feedback)
[Judge]
    ├→ Accept? → [END - Return refined idea]
    └→ Iterate? → [LOOP back to Creator with feedback]

Maximum iterations: 5 (configurable)
Acceptance threshold: Fitness ≥ 0.55
```

## Performance Considerations

### Optimization Tips

1. **Use cheaper models for initial iterations**
   - Creator: gpt-3.5-turbo for quick ideas
   - Critic: gpt-4-turbo for accuracy only on iterations 3+

2. **Batch processing**
   - Process multiple workflows in parallel
   - Monitor token usage and Redis queue depth

3. **Caching**
   - Leverage memory system for similar problems
   - Mark accepted ideas for future reference

4. **Streaming**
   - Use WebSocket for real-time monitoring
   - Reduces polling overhead

## Monitoring and Debugging

### Health Checks

```bash
# Overall health
curl http://localhost:8000/health

# Dependency health
curl http://localhost:8000/health/dependencies

# Configuration
curl http://localhost:8000/debug/config
```

### View Logs

Check application logs for:
- Agent outputs and reasoning
- Token usage per iteration
- Database and Redis operations
- Error traces

## Advanced Features

### Custom Agent Development

Extend `BaseAgent` to create custom agents:

```python
from app.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, custom_model_mapping=None):
        super().__init__("custom", custom_model_mapping)
    
    async def execute(self, input_data, **kwargs):
        # Your custom logic
        pass
```

### Hooking into Workflow

Modify `WorkflowOrchestrator.graph` to insert custom nodes or adjust edges.

### Extending Metrics

Add custom metrics in `MetricsEngine` by extending calculation methods.

## Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Settings

```bash
# Use production ASGI server
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app

# Or with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Testing

```bash
# Run with test configuration
pytest tests/ -v

# Integration tests with real APIs
pytest tests/integration -v
```

## Troubleshooting

### Issue: "API key not found"
**Solution**: Check `.env` and ensure `OPENAI_API_KEY` is set

### Issue: "Database connection refused"
**Solution**: Ensure PostgreSQL is running and `DB_*` variables are correct

### Issue: "Redis connection failed"
**Solution**: Ensure Redis is running on configured host/port

### Issue: "Workflow timeout"
**Solution**: Check token usage; increase `max_iterations` or reduce complexity

## Performance Metrics

Expected metrics for typical workflow:

- **Execution time**: 30-120 seconds (excluding LLM latency)
- **Tokens per iteration**: 1000-2000 (varies by model)
- **Memory usage**: 200-500 MB
- **Redis message throughput**: 50-200 msg/sec
- **Database writes**: 10-50 per workflow

## Contributing

To extend the system:

1. Add new agent in `app/agents/`
2. Update `WorkflowOrchestrator` graph
3. Register metrics if needed
4. Test with sample workflows

## License

Proprietary - AI System Development

## Support

For issues, questions, or feature requests, contact the development team.

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: Production Ready
