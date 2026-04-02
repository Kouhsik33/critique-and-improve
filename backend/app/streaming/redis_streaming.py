"""
Redis-based streaming for real-time agent events.
Publishes agent actions and updates to subscribed clients.
"""

import json
import asyncio
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
import redis.asyncio as aioredis
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

from app.schemas.state_schema import StreamEvent, AgentAction


class RedisSettings(BaseSettings):
    """Redis configuration"""
    model_config = ConfigDict(extra="ignore", env_file=".env", case_sensitive=False)
    
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None


class RedisStreamManager:
    """Manages Redis pub/sub for streaming agent events"""
    
    _instance: Optional["RedisStreamManager"] = None
    _redis: Optional[aioredis.Redis] = None
    _settings: RedisSettings = None
    _subscribers: Dict[str, List[Callable]] = {}
    
    def __new__(cls, settings: Optional[RedisSettings] = None):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = settings or RedisSettings()
        return cls._instance
    
    async def connect(self):
        """Connect to Redis"""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                f"redis://:{self._settings.redis_password}@{self._settings.redis_host}:{self._settings.redis_port}/{self._settings.redis_db}"
                if self._settings.redis_password
                else f"redis://{self._settings.redis_host}:{self._settings.redis_port}/{self._settings.redis_db}",
                encoding="utf8",
                decode_responses=True,
            )
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    async def publish_event(
        self,
        request_id: str,
        event: StreamEvent,
    ):
        """Publish an agent event"""
        await self.connect()
        
        channel = f"workflow:{request_id}"
        message = json.loads(event.model_dump_json())
        
        await self._redis.publish(channel, json.dumps(message))
    
    async def publish_agent_action(
        self,
        request_id: str,
        agent: str,
        action: AgentAction,
        data: Dict[str, Any],
        iteration: int,
    ):
        """Publish an agent action"""
        event = StreamEvent(
            type="agent_action",
            agent=agent,
            action=action,
            data=data,
            iteration=iteration,
            request_id=request_id,
        )
        await self.publish_event(request_id, event)
    
    async def publish_feedback(
        self,
        request_id: str,
        feedback_data: Dict[str, Any],
        iteration: int,
    ):
        """Publish feedback to the client"""
        event = StreamEvent(
            type="feedback",
            agent="judge",
            action=AgentAction.JUDGE,
            data=feedback_data,
            iteration=iteration,
            request_id=request_id,
        )
        await self.publish_event(request_id, event)
    
    async def publish_workflow_complete(
        self,
        request_id: str,
        final_output: str,
        total_iterations: int,
        metrics: Dict[str, Any],
    ):
        """Publish workflow completion"""
        event = StreamEvent(
            type="workflow_complete",
            agent="system",
            action=AgentAction.JUDGE,
            data={
                "final_output": final_output,
                "total_iterations": total_iterations,
                "metrics": metrics,
            },
            iteration=total_iterations,
            request_id=request_id,
        )
        await self.publish_event(request_id, event)
    
    async def subscribe(
        self,
        request_id: str,
        callback: Callable,
    ) -> "RedisSubscriber":
        """Subscribe to workflow events"""
        await self.connect()
        channel = f"workflow:{request_id}"
        
        subscriber = RedisSubscriber(self._redis, channel, callback)
        await subscriber.start()
        
        return subscriber
    
    async def store_state(self, request_id: str, state: Dict[str, Any]):
        """Store workflow state in Redis for persistence"""
        await self.connect()
        key = f"state:{request_id}"
        await self._redis.set(key, json.dumps(state, default=str), ex=86400)  # 24 hour TTL
    
    async def get_state(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve workflow state"""
        await self.connect()
        key = f"state:{request_id}"
        state_json = await self._redis.get(key)
        if state_json:
            return json.loads(state_json)
        return None
    
    async def store_metrics(self, request_id: str, metrics: Dict[str, Any]):
        """Store metrics in Redis"""
        await self.connect()
        key = f"metrics:{request_id}"
        await self._redis.set(key, json.dumps(metrics, default=str), ex=86400)
    
    async def get_metrics(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve metrics"""
        await self.connect()
        key = f"metrics:{request_id}"
        metrics_json = await self._redis.get(key)
        if metrics_json:
            return json.loads(metrics_json)
        return None


class RedisSubscriber:
    """Manages a subscription to workflow events"""
    
    def __init__(
        self,
        redis_client: aioredis.Redis,
        channel: str,
        callback: Callable,
    ):
        self.redis_client = redis_client
        self.channel = channel
        self.callback = callback
        self.pubsub = None
        self.task = None
    
    async def start(self):
        """Start listening to the channel"""
        self.pubsub = self.redis_client.pubsub()
        await self.pubsub.subscribe(self.channel)
        self.task = asyncio.create_task(self._listen())
    
    async def _listen(self):
        """Listen for messages"""
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await self.callback(data)
                except Exception as e:
                    print(f"Error in subscription callback: {e}")
    
    async def stop(self):
        """Stop listening"""
        if self.pubsub:
            await self.pubsub.unsubscribe(self.channel)
            await self.pubsub.close()
        if self.task:
            self.task.cancel()
