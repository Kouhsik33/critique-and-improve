"""
WebSocket streaming for real-time client updates.
"""

import json
from typing import Set
import asyncio

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """Manages WebSocket connections for real-time streaming"""
    
    def __init__(self):
        self.active_connections: dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, request_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        if request_id not in self.active_connections:
            self.active_connections[request_id] = set()
        
        self.active_connections[request_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, request_id: str):
        """Remove a disconnected WebSocket"""
        if request_id in self.active_connections:
            self.active_connections[request_id].discard(websocket)
            
            if not self.active_connections[request_id]:
                del self.active_connections[request_id]
    
    async def broadcast(self, request_id: str, message: dict):
        """Broadcast a message to all connected clients for a workflow"""
        if request_id not in self.active_connections:
            return
        
        # Send to all connections
        disconnected = set()
        for connection in self.active_connections[request_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending message: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn, request_id)
    
    async def send_to_connection(self, websocket: WebSocket, message: dict):
        """Send a message to a specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending to connection: {e}")
    
    def get_active_connections(self, request_id: str) -> int:
        """Get count of active connections"""
        if request_id in self.active_connections:
            return len(self.active_connections[request_id])
        return 0


# Global connection manager
connection_manager = ConnectionManager()
