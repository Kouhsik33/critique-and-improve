"""
FastAPI application with API endpoints for multi-agent workflow.
"""

from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import json

from app.schemas.state_schema import RunRequest
from app.services.execution_service import ExecutionService
from app.streaming.websocket import connection_manager
from app.streaming.redis_streaming import RedisStreamManager
from app.db.postgres import DatabaseManager


# Application state
execution_service = None
redis_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global execution_service, redis_manager
    
    # Startup
    print("Initializing application...")
    DatabaseManager.init()
    execution_service = ExecutionService()
    redis_manager = RedisStreamManager()
    await redis_manager.connect()
    print("Application initialized successfully")
    
    yield
    
    # Shutdown
    print("Shutting down application...")
    await redis_manager.disconnect()
    print("Application shut down")


# Create FastAPI app
app = FastAPI(
    title="Multi-Agent AI System",
    description="Production-grade backend for collaborative multi-agent intelligence",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "multi-agent-ai-backend",
        "version": "1.0.0",
    }


@app.post("/run")
async def run_workflow(request: RunRequest, background_tasks: BackgroundTasks):
    """
    Start a new workflow execution.
    
    Request:
    {
        "prompt": "Your idea/problem to iterate on",
        "max_iterations": 5,
        "model_mapping": {
            "creator": "gpt-4",
            "critic": "gpt-4-turbo",
            ...
        },
        "temperature": 0.7
    }
    
    Response:
    {
        "request_id": "unique identifier",
        "status": "started",
        "message": "Workflow is running..."
    }
    """
    try:
        import uuid
        request_id = f"run_{uuid.uuid4().hex[:12]}"
        
        # Start workflow in background
        async def run_in_background():
            try:
                await execution_service.execute(request)
            except Exception as e:
                print(f"Background workflow error: {e}")
        
        background_tasks.add_task(run_in_background)
        
        return {
            "request_id": request_id,
            "status": "started",
            "message": "Workflow execution started",
            "prompt": request.prompt[:100] + "..." if len(request.prompt) > 100 else request.prompt,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/{request_id}")
async def get_metrics(request_id: str):
    """
    Get metrics for a completed workflow.
    
    Response:
    {
        "agent_metrics": [...],
        "idea_metrics": [...],
        "system_metrics": [...]
    }
    """
    try:
        metrics = await execution_service.get_metrics(request_id)
        if not metrics:
            raise HTTPException(status_code=404, detail="Metrics not found")
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/stream/{request_id}")
async def websocket_stream(websocket: WebSocket, request_id: str):
    """
    WebSocket endpoint for real-time streaming of agent events.
    
    Events streamed:
    {
        "type": "agent_action|feedback|workflow_complete",
        "agent": "creator|critic|radical|synthesizer|judge",
        "action": "generate|attack|disrupt|merge|judge",
        "data": {...},
        "iteration": 0
    }
    """
    await connection_manager.connect(websocket, request_id)
    
    try:
        # Subscribe to Redis events
        redis_manager = RedisStreamManager()
        
        async def handle_redis_message(message):
            """Handle incoming Redis message"""
            await connection_manager.send_to_connection(websocket, message)
        
        subscriber = await redis_manager.subscribe(request_id, handle_redis_message)
        
        # Keep connection open
        while True:
            # Wait for client messages (for ping/pong)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                # Send periodic pings to keep connection alive
                await websocket.send_json({"type": "ping"})
            except Exception:
                break
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        connection_manager.disconnect(websocket, request_id)
        if 'subscriber' in locals():
            await subscriber.stop()


@app.get("/status/{request_id}")
async def get_status(request_id: str):
    """
    Get current status of a workflow.
    
    Response:
    {
        "request_id": "...",
        "status": "running|completed|failed",
        "iteration": 2,
        "connected_clients": 3
    }
    """
    try:
        # Get workflow status from database
        session = DatabaseManager.get_session()
        try:
            from app.db.postgres import WorkflowLog
            workflow = session.query(WorkflowLog).filter_by(request_id=request_id).first()
            
            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            return {
                "request_id": request_id,
                "status": workflow.status,
                "initial_prompt": workflow.initial_prompt[:100] + "..." if workflow.initial_prompt else "",
                "final_output": workflow.final_output[:100] + "..." if workflow.final_output else "",
                "total_iterations": workflow.total_iterations or 0,
                "total_tokens": workflow.total_tokens or 0,
                "connected_clients": connection_manager.get_active_connections(request_id),
                "created_at": workflow.created_at.isoformat(),
                "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            }
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ideas/{workflow_id}/search")
async def search_similar_ideas(workflow_id: str, query: str):
    """
    Search for similar ideas from memory.
    
    Query parameters:
    - query: Search query string
    
    Response:
    {
        "results": [
            {
                "idea": "...",
                "similarity_score": 0.85,
                "metadata": {...}
            }
        ]
    }
    """
    try:
        from app.memory.vector_store import MemoryStore
        memory = MemoryStore()
        results = memory.search_similar_ideas(query, workflow_id, k=5)
        
        return {
            "query": query,
            "workflow_id": workflow_id,
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/evolution/{workflow_id}")
async def get_evolution_history(workflow_id: str):
    """
    Get the evolution history of ideas in a workflow.
    
    Response:
    {
        "workflow_id": "...",
        "history": [
            {
                "iteration": 0,
                "type": "idea",
                "content": "..."
            }
        ]
    }
    """
    try:
        from app.memory.vector_store import MemoryStore
        memory = MemoryStore()
        history = memory.get_evolution_history(workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "history_count": len(history),
            "history": history,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health check for dependencies
# ============================================================================

@app.get("/health/dependencies")
async def health_check_dependencies():
    """Check status of all dependencies"""
    status = {
        "database": "unknown",
        "redis": "unknown",
        "llm": "unknown",
    }
    
    # Check database
    try:
        session = DatabaseManager.get_session()
        session.close()
        status["database"] = "ok"
    except Exception as e:
        status["database"] = f"error: {str(e)}"
    
    # Check Redis
    try:
        redis_mgr = RedisStreamManager()
        await redis_mgr.connect()
        status["redis"] = "ok"
        await redis_mgr.disconnect()
    except Exception as e:
        status["redis"] = f"error: {str(e)}"
    
    # Check LLM
    try:
        from app.config.llm_config import LLMFactory
        LLMFactory.get_settings()
        status["llm"] = "ok"
    except Exception as e:
        status["llm"] = f"error: {str(e)}"
    
    return {
        "status": "healthy" if all(v == "ok" for v in status.values()) else "degraded",
        "dependencies": status,
    }


# ============================================================================
# Debug endpoints (remove in production)
# ============================================================================

@app.get("/debug/config")
async def debug_config():
    """Get current configuration (debug only)"""
    try:
        from app.config.llm_config import LLMFactory
        settings = LLMFactory.get_settings()
        
        return {
            "models": {
                "creator": settings.creator_model,
                "critic": settings.critic_model,
                "radical": settings.radical_model,
                "synthesizer": settings.synthesizer_model,
                "judge": settings.judge_model,
            },
            "temperatures": {
                "creator": settings.creator_temperature,
                "critic": settings.critic_temperature,
                "radical": settings.radical_temperature,
                "synthesizer": settings.synthesizer_temperature,
                "judge": settings.judge_temperature,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
