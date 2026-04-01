# Multi-Agent AI System - API Reference Guide

## Base URL

```
http://localhost:8000
```

## Authentication

Currently no authentication required (add for production).

## Content-Type

All endpoints use `application/json` unless specified.

---

## Endpoints

### 1. Health Check

**GET** `/health`

Check if the backend is running.

```bash
curl http://localhost:8000/health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "multi-agent-ai-backend",
  "version": "1.0.0"
}
```

---

### 2. Start Workflow

**POST** `/run`

Initiate a new workflow execution.

**Request Body**:
```json
{
  "prompt": "Your problem or idea to iterate on",
  "max_iterations": 5,
  "temperature": 0.7,
  "include_reasoning": true,
  "model_mapping": {
    "creator": "gpt-4-turbo",
    "critic": "gpt-4-turbo",
    "radical": "gpt-4",
    "synthesizer": "gpt-3.5-turbo",
    "judge": "gpt-4"
  }
}
```

**Field Documentation**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `prompt` | string | required | The idea or problem to iterate on |
| `max_iterations` | integer | 5 | Maximum refinement cycles (1-10) |
| `temperature` | float | 0.7 | Creativity level (0.0-1.0) |
| `include_reasoning` | boolean | true | Include agent reasoning in output |
| `model_mapping` | object | defaults | Custom models per agent |

**Model Mapping Options**:
```json
{
  "creator": "gpt-4-turbo|gpt-4|gpt-3.5-turbo|claude-3-opus|gemini-pro",
  "critic": "gpt-4-turbo|gpt-4|claude-3-opus",
  "radical": "gpt-4|gpt-3.5-turbo|claude-3-sonnet",
  "synthesizer": "gpt-3.5-turbo|gpt-4|claude-3-haiku",
  "judge": "gpt-4|gpt-4-turbo|claude-3-opus"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "How can we make education more accessible to remote areas?",
    "max_iterations": 3,
    "temperature": 0.7
  }'
```

**Response** (200 OK):
```json
{
  "request_id": "run_abc12345678",
  "status": "started",
  "message": "Workflow execution started",
  "prompt": "How can we make education more accessible..."
}
```

**Error Responses**:
- 400: Invalid request body
- 500: Server error

---

### 3. Workflow Status

**GET** `/status/{request_id}`

Get current status of a workflow.

**Parameters**:
- `request_id` (path): The workflow request ID from `/run`

**Example**:
```bash
curl http://localhost:8000/status/run_abc12345678
```

**Response** (200 OK):
```json
{
  "request_id": "run_abc12345678",
  "status": "completed|running|failed",
  "initial_prompt": "How can we make education...",
  "final_output": "Refined solution with integrated feedback...",
  "total_iterations": 3,
  "total_tokens": 4250,
  "connected_clients": 2,
  "created_at": "2024-01-15T10:30:45.123456",
  "completed_at": "2024-01-15T10:35:20.654321"
}
```

**Status Values**:
- `running`: Workflow in progress
- `completed`: Successfully finished
- `failed`: Encountered an error

---

### 4. Metrics

**GET** `/metrics/{request_id}`

Get detailed metrics for a completed workflow.

**Parameters**:
- `request_id` (path): The workflow request ID

**Example**:
```bash
curl http://localhost:8000/metrics/run_abc12345678
```

**Response** (200 OK):
```json
{
  "idea_metrics": [
    {
      "novelty": 0.82,
      "feasibility": 0.65,
      "clarity": 0.78,
      "impact": 0.75,
      "fitness_score": 0.75
    },
    {
      "novelty": 0.85,
      "feasibility": 0.70,
      "clarity": 0.80,
      "impact": 0.78,
      "fitness_score": 0.78
    }
  ],
  "agent_metrics": {
    "creator": [
      {
        "token_count": 320,
        "quality_score": 0.78,
        "confidence": 0.72
      }
    ],
    "critic": [
      {
        "token_count": 280,
        "quality_score": 0.82,
        "confidence": 0.80
      }
    ],
    "radical": [
      {
        "token_count": 250,
        "quality_score": 0.70,
        "confidence": 0.65
      }
    ],
    "synthesizer": [
      {
        "token_count": 350,
        "quality_score": 0.85,
        "confidence": 0.82
      }
    ],
    "judge": [
      {
        "token_count": 200,
        "quality_score": 0.90,
        "confidence": 0.88
      }
    ]
  },
  "system_metrics": {
    "iteration_count": 3,
    "convergence_speed": 0.18,
    "total_token_usage": 4250,
    "conflict_intensity": 0.42,
    "token_efficiency": 1416.67
  }
}
```

**Metrics Explanation**:

| Metric | Range | Meaning |
|--------|-------|---------|
| `novelty` | 0-1 | Uniqueness of idea |
| `feasibility` | 0-1 | Practical viability |
| `clarity` | 0-1 | Communication quality |
| `impact` | 0-1 | Potential effectiveness |
| `fitness_score` | 0-1 | Composite quality score |
| `token_count` | 0-∞ | API tokens used |
| `quality_score` | 0-1 | Output quality rating |
| `confidence` | 0-1 | Agent confidence |
| `convergence_speed` | 0-1 | Rate of improvement |
| `conflict_intensity` | 0-1 | Disagreement between agents |

---

### 5. Real-Time Streaming (WebSocket)

**WS** `/stream/{request_id}`

Subscribe to real-time agent events.

**Parameters**:
- `request_id` (path): The workflow request ID

**Example** (using wscat):
```bash
wscat -c ws://localhost:8000/stream/run_abc12345678
```

**Example** (using JavaScript):
```javascript
const ws = new WebSocket('ws://localhost:8000/stream/run_abc12345678');

ws.addEventListener('open', () => {
  console.log('Connected');
});

ws.addEventListener('message', (event) => {
  const message = JSON.parse(event.data);
  console.log(`Agent: ${message.agent}, Action: ${message.action}`);
});

ws.addEventListener('close', () => {
  console.log('Disconnected');
});
```

**Event Messages**:

**Agent Action Event**:
```json
{
  "type": "agent_action",
  "agent": "creator",
  "action": "generate",
  "data": {
    "ideas": "Generated novel approaches to the problem"
  },
  "iteration": 0,
  "timestamp": "2024-01-15T10:30:50.123456"
}
```

**Feedback Event**:
```json
{
  "type": "feedback",
  "agent": "judge",
  "action": "judge",
  "data": {
    "fitness_score": 0.72,
    "should_iterate": true,
    "issues": [
      {
        "category": "feasibility",
        "severity": "medium",
        "description": "Resource requirements need clarification"
      }
    ]
  },
  "iteration": 0,
  "timestamp": "2024-01-15T10:31:00.123456"
}
```

**Workflow Complete Event**:
```json
{
  "type": "workflow_complete",
  "agent": "system",
  "action": "judge",
  "data": {
    "final_output": "Complete refined idea...",
    "total_iterations": 3,
    "metrics": {...}
  },
  "iteration": 3,
  "timestamp": "2024-01-15T10:35:20.123456"
}
```

**Agent Actions**:
- `generate`: Agent created output
- `attack`: Critic found issues
- `disrupt`: Radical challenges assumptions
- `merge`: Synthesizer integrated feedback
- `judge`: Judge evaluated quality

---

### 6. Search Similar Ideas

**POST** `/ideas/{workflow_id}/search`

Search for similar ideas in memory across workflows.

**Parameters**:
- `workflow_id` (path): The workflow ID to search within

**Request Body**:
```json
{
  "query": "keyword or phrase to search for"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/ideas/exec_abcdefg123/search \
  -H "Content-Type: application/json" \
  -d '{"query": "technology based educational solutions"}'
```

**Response** (200 OK):
```json
{
  "query": "technology based educational solutions",
  "workflow_id": "exec_abcdefg123",
  "results": [
    {
      "content": "Use AI-powered tutoring systems to provide personalized learning paths...",
      "similarity_score": 0.92,
      "metadata": {
        "type": "idea",
        "iteration": 1,
        "agent": "creator"
      }
    },
    {
      "content": "Implement peer-to-peer learning networks using blockchain for credibility...",
      "similarity_score": 0.85,
      "metadata": {
        "type": "idea",
        "iteration": 2,
        "agent": "radical"
      }
    }
  ]
}
```

---

### 7. Evolution History

**GET** `/evolution/{workflow_id}`

Get the complete evolution history of ideas in a workflow.

**Parameters**:
- `workflow_id` (path): The workflow ID

**Example**:
```bash
curl http://localhost:8000/evolution/exec_abcdefg123
```

**Response** (200 OK):
```json
{
  "workflow_id": "exec_abcdefg123",
  "history_count": 8,
  "history": [
    {
      "type": "idea",
      "iteration": 0,
      "agent": "creator",
      "idea": "Initial idea about online learning platforms..."
    },
    {
      "type": "critique",
      "iteration": 0,
      "category": "feasibility",
      "severity": 0.6,
      "description": "High infrastructure costs in developing regions"
    },
    {
      "type": "idea",
      "iteration": 1,
      "agent": "radical",
      "idea": "What if we used mesh networks instead of centralized servers..."
    }
  ]
}
```

---

### 8. Health Check (Dependencies)

**GET** `/health/dependencies`

Check status of all external dependencies.

**Example**:
```bash
curl http://localhost:8000/health/dependencies
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "dependencies": {
    "database": "ok",
    "redis": "ok",
    "llm": "ok"
  }
}
```

**Degraded Response** (200 OK):
```json
{
  "status": "degraded",
  "dependencies": {
    "database": "ok",
    "redis": "error: Connection refused",
    "llm": "ok"
  }
}
```

---

### 9. Configuration (Debug)

**GET** `/debug/config`

Get current LLM configuration (debug endpoint).

**Example**:
```bash
curl http://localhost:8000/debug/config
```

**Response** (200 OK):
```json
{
  "models": {
    "creator": "gpt-4-turbo",
    "critic": "gpt-4-turbo",
    "radical": "gpt-4",
    "synthesizer": "gpt-3.5-turbo",
    "judge": "gpt-4"
  },
  "temperatures": {
    "creator": 0.8,
    "critic": 0.5,
    "radical": 0.9,
    "synthesizer": 0.6,
    "judge": 0.3
  }
}
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error - Server issue |
| 503 | Service Unavailable - Dependency down |

### Example Error Response

```json
{
  "detail": "Metrics not found for request_id: invalid_id"
}
```

---

## Rate Limiting

Currently no rate limiting (add for production).

---

## Pagination

Endpoints with large responses can be paginated (implement as needed).

---

## Versioning

Current API version: 1.0.0

---

## OpenAPI Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Examples by Use Case

### Use Case 1: Iterative Idea Refinement

```bash
# 1. Start workflow
RESPONSE=$(curl -s -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Improve remote collaboration tools",
    "max_iterations": 5
  }')
REQUEST_ID=$(echo $RESPONSE | jq -r '.request_id')

# 2. Monitor progress
watch -n 2 "curl -s http://localhost:8000/status/$REQUEST_ID | jq '.status'"

# 3. Stream live events
wscat -c ws://localhost:8000/stream/$REQUEST_ID

# 4. Get final metrics
curl http://localhost:8000/metrics/$REQUEST_ID
```

### Use Case 2: Custom Model Selection

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Design a sustainable food system",
    "max_iterations": 3,
    "model_mapping": {
      "creator": "gpt-4",
      "critic": "claude-3-opus",
      "radical": "gpt-4",
      "synthesizer": "gpt-3.5-turbo",
      "judge": "claude-3-opus"
    }
  }'
```

### Use Case 3: Knowledge Search

```bash
# Start workflow
REQUEST_ID="exec_abcdef123"

# Search for similar ideas
curl -X POST http://localhost:8000/ideas/$REQUEST_ID/search \
  -H "Content-Type: application/json" \
  -d '{"query": "sustainability environmental impact"}'

# Get evolution
curl http://localhost:8000/evolution/$REQUEST_ID
```

---

## Best Practices

1. **Always check health first**: `GET /health`
2. **Use WebSocket for monitoring**: Subscribe to `/stream/{request_id}`
3. **Check metrics after completion**: `GET /metrics/{request_id}`
4. **Custom models for cost**: Use cheaper models for initial iterations
5. **Search before running**: Check similar ideas to avoid duplication
6. **Monitor token usage**: Track metrics to optimize costs

---

## Support

For API issues, check:
1. `/health` endpoint
2. `/health/dependencies` for service status
3. Application logs
4. Backend README.md documentation

---

**API Version**: 1.0.0  
**Last Updated**: 2024
