# IDEA ARENA Frontend

React (Vite) frontend for the multi-agent backend in `../backend`.

## Backend API Contract

This frontend is aligned to the backend API described in `backend/README.md`.

- `POST /run` starts a workflow and returns `request_id`
- `WS /stream/{request_id}` streams real-time workflow events
- `GET /metrics/{request_id}` returns workflow metrics
- `GET /status/{request_id}` returns workflow status

## Event Handling

WebSocket event shapes consumed by the UI:

- `agent_action` events with:
  - `agent`
  - `action` (`generate | attack | disrupt | merge | judge`)
  - `data`
  - `iteration`
- `feedback`
- `iteration_complete`
- `workflow_complete`

## Frontend Flow

1. User enters a prompt and clicks **Start**
2. Frontend calls `POST /run`
3. Frontend stores `request_id`
4. Frontend opens WebSocket: `/stream/{request_id}`
5. Frontend polls:
   - `/metrics/{request_id}` every 2s
   - `/status/{request_id}` every 2s
6. UI updates global state in real-time

## Configuration

Set API URL with Vite env var:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

If not set, frontend defaults to `http://localhost:8000`.

## Development

```bash
npm install
npm run dev
```

Open `http://localhost:5173`.

## Key Files

- `src/services/api.js` - request-id scoped REST API helpers
- `src/hooks/useAgentStream.js` - WebSocket + metrics/status polling
- `src/context/AppContext.jsx` - global state + stream reducer
- `src/App.jsx` - run lifecycle and top-level layout
