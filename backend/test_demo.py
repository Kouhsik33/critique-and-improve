"""
Test script to demonstrate the multi-agent AI system.
Run: python test_demo.py
"""

import requests
import json
import asyncio
import websockets
import time
from typing import Tuple, Optional
from datetime import datetime

API_BASE = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("\n" + "="*50)
    print("Testing Health Check")
    print("="*50)
    
    response = requests.get(f"{API_BASE}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_dependencies():
    """Test dependency health"""
    print("\n" + "="*50)
    print("Testing Dependencies")
    print("="*50)
    
    response = requests.get(f"{API_BASE}/health/dependencies")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_config():
    """Test configuration endpoint"""
    print("\n" + "="*50)
    print("Testing Configuration")
    print("="*50)
    
    response = requests.get(f"{API_BASE}/debug/config")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_workflow():
    """Test workflow execution"""
    print("\n" + "="*50)
    print("Testing Workflow Execution")
    print("="*50)
    
    payload = {
        "prompt": "How can we make education more accessible to remote areas using technology?",
        "max_iterations": 3,
        "temperature": 0.7,
        "model_mapping": {
            "creator": "gpt-4o-mini",
            "critic": "gpt-4o-mini",
            "radical": "gpt-4o-mini",
            "synthesizer": "gpt-4o-mini",
            "judge": "gpt-4o-mini"
        }
    }
    
    print(f"Starting workflow with prompt: {payload['prompt'][:50]}...")
    
    response = requests.post(f"{API_BASE}/run", json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    return result.get("request_id")


def test_status(request_id: str):
    """Test workflow status"""
    print("\n" + "="*50)
    print(f"Testing Status for {request_id}")
    print("="*50)
    
    response = requests.get(f"{API_BASE}/status/{request_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Workflow may still be processing or doesn't exist yet")


def test_metrics(request_id: str):
    """Test metrics retrieval with detailed agent outputs"""
    print("\n" + "="*80)
    print(f"DETAILED AGENT OUTPUTS & METRICS for {request_id}")
    print("="*80)
    
    response = requests.get(f"{API_BASE}/metrics/{request_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        metrics = response.json()
        
        # Display agent metrics
        agent_metrics = metrics.get('agent_metrics', [])
        print(f"\n📊 AGENT METRICS: {len(agent_metrics)} entries")
        print("-" * 80)
        
        if agent_metrics:
            for i, metric in enumerate(agent_metrics):
                print(f"\n[AGENT {i+1}] {metric.get('agent', 'unknown').upper()}")
                print(f"  • Iteration: {metric.get('iteration')}")
                print(f"  • Action: {metric.get('action')}")
                print(f"  • Quality Score: {metric.get('quality_score'):.2f}")
                print(f"  • Confidence: {metric.get('confidence'):.2f}")
                print(f"  • Tokens Used: {metric.get('token_count')}")
                print(f"  • Latency: {metric.get('latency_ms', 0):.0f}ms")
                
                # Display output if available
                output = metric.get('output')
                if output:
                    print(f"\n  📝 OUTPUT:")
                    # Truncate long outputs
                    if len(output) > 500:
                        print(f"  {output[:500]}...")
                    else:
                        print(f"  {output}")
        else:
            print("  ⏳ No agent metrics yet (workflow still processing or failed)")
        
        # Display idea metrics
        idea_metrics = metrics.get('idea_metrics', [])
        print(f"\n\n💡 IDEA METRICS: {len(idea_metrics)} ideas")
        print("-" * 80)
        
        if idea_metrics:
            for i, idea in enumerate(idea_metrics):
                print(f"\n[IDEA {i+1}] (Iteration {idea.get('iteration')})")
                print(f"  📌 {idea.get('idea', 'N/A')[:150]}")
                print(f"  • Novelty: {idea.get('novelty', 0):.2f} | Feasibility: {idea.get('feasibility', 0):.2f}")
                print(f"  • Clarity: {idea.get('clarity', 0):.2f} | Impact: {idea.get('impact', 0):.2f}")
                print(f"  • Fitness Score: {idea.get('fitness_score', 0):.2f}")
        else:
            print("  ⏳ No ideas generated yet")
        
        # Display system metrics
        system_metrics = metrics.get('system_metrics', [])
        print(f"\n\n⚙️  SYSTEM METRICS: {len(system_metrics)} entries")
        print("-" * 80)
        
        if system_metrics:
            for metric in system_metrics:
                print(f"\n  • Iterations: {metric.get('iteration_count')}")
                print(f"  • Total Tokens: {metric.get('total_token_usage')}")
                print(f"  • Convergence Speed: {metric.get('convergence_speed', 'N/A')}")
                print(f"  • Conflict Intensity: {metric.get('conflict_intensity', 0):.2f}")
        else:
            print("  ⏳ No system metrics yet")
    else:
        print(f"❌ Metrics not available (Status: {response.status_code})")



def test_search(workflow_id: str):
    """Test idea search"""
    print("\n" + "="*50)
    print(f"Testing Idea Search for {workflow_id}")
    print("="*50)
    
    response = requests.post(
        f"{API_BASE}/ideas/{workflow_id}/search?query=technology education"
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_evolution(workflow_id: str):
    """Test evolution history"""
    print("\n" + "="*50)
    print(f"Testing Evolution History for {workflow_id}")
    print("="*50)
    
    response = requests.get(f"{API_BASE}/evolution/{workflow_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"History count: {data.get('history_count')}")
        for i, item in enumerate(data.get('history', [])[:3]):
            print(f"  [{i}] Type: {item.get('type')}, Iteration: {item.get('iteration')}")


async def stream_websocket(request_id: str, duration: int = 30):
    """Stream WebSocket events for a fixed duration (seconds)"""
    print("\n" + "="*50)
    print(f"Streaming WebSocket for {request_id} ({duration}s)")
    print("="*50)
    
    ws_url = f"ws://localhost:8000/stream/{request_id}"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("Connected to WebSocket")

            end_time = time.time() + duration
            while time.time() < end_time:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(response)
                    event_type = data.get("type", "unknown")
                    agent = data.get("agent", "unknown")
                    action = data.get("action", "unknown")
                    iteration = data.get("iteration", "?")
                    print(f"[{event_type}] {agent}::{action} (iter {iteration})")

                    output = data.get("data", {}).get("output")
                    if output:
                        preview = output[:200] + ("..." if len(output) > 200 else "")
                        print(f"  output: {preview}")

                    if event_type == "workflow_complete":
                        break
                except asyncio.TimeoutError:
                    await websocket.send("ping")
    except Exception as e:
        print(f"WebSocket connection failed (expected if workflow not running): {e}")


def wait_for_completion(request_id: str, timeout: int = 120, interval: int = 5) -> Tuple[str, Optional[dict]]:
    """Poll workflow status until completed/failed or timeout"""
    start = time.time()
    last_payload = None
    while time.time() - start < timeout:
        response = requests.get(f"{API_BASE}/status/{request_id}")
        if response.status_code == 200:
            payload = response.json()
            last_payload = payload
            status = payload.get("status")
            if status in ("completed", "failed"):
                return status, payload
            print(f"  ⏳ Workflow still {status}... waiting {interval}s")
        else:
            print("  ⚠️  Status not ready yet")
        time.sleep(interval)
    return "timeout", last_payload


def main():
    """Run all tests"""
    print("\n")
    print("╔════════════════════════════════════════════════════════╗")
    print("║  Multi-Agent AI System - Test Suite                   ║")
    print("║  Make sure the backend is running on localhost:8000   ║")
    print("╚════════════════════════════════════════════════════════╝")
    
    try:
        # Test endpoints
        test_health()
        test_dependencies()
        test_config()
        
        # Start workflow
        request_id = test_workflow()
        
        # Stream live events while workflow runs
        if request_id:
            asyncio.run(stream_websocket(request_id, duration=30))

        # Wait for workflow to complete
        print("\nWaiting for workflow to process...")
        if request_id:
            status, payload = wait_for_completion(request_id, timeout=120, interval=5)
            print(f"Final status: {status}")
            if payload:
                print(f"Completed at: {payload.get('completed_at')}")
        
        # Test status and metrics
        if request_id:
            test_status(request_id)
            test_metrics(request_id)
            test_search(request_id)
            test_evolution(request_id)
        
        print("\n" + "="*50)
        print("✓ Test suite completed")
        print("="*50)
        print("\nNext steps:")
        print("1. Monitor the workflow at /status/{request_id}")
        print("2. Watch real-time updates at /stream/{request_id}")
        print("3. Check metrics at /metrics/{request_id}")
        print(f"\nYour request ID: {request_id}")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API at localhost:8000")
        print("Make sure the backend is running:")
        print("  uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
