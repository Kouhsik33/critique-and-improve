import asyncio
from app.schemas.state_schema import RunRequest
from app.services.execution_service import ExecutionService

async def main():
    service = ExecutionService()
    request = RunRequest(
        prompt="How can we make education more accessible to remote areas using technology?",
        max_iterations=3,
        temperature=0.7,
        model_mapping={
            "creator": "gpt-4o-mini",
            "critic": "gpt-4o-mini",
            "radical": "gpt-4o-mini",
            "synthesizer": "gpt-4o-mini",
            "judge": "gpt-4o-mini"
        }
    )
    try:
        await service.execute(request, request_id="test_local_run")
        print("Success!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
