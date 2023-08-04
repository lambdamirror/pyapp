from itertools import chain
from typing import Dict, List

from _documents.users.schema import UserList
from bson import ObjectId
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from utils.logger import logger

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[ObjectId, List[WebSocket]] = {}
        self.stream_by_role = {

        }

    async def connect(self, user: UserList, websocket: WebSocket):
        await websocket.accept()
        logger.info(f"[Websocket] connect {user.email}")
        if user.id not in self.active_connections:
            self.active_connections[user.id] = []
        self.active_connections[user.id].append(websocket)

    def disconnect(self, user: UserList, websocket: WebSocket):
        logger.info(f"[Websocket] disconnect {user.email}")
        if user.id in self.active_connections:
            self.active_connections[user.id].remove(websocket)

    def subscribe(self, websocket: WebSocket, data: dict):
        logger.info(f"[Websocket] subscribe {websocket}")
        if websocket in self.active_connections and data['']:
            pass

    def unsubscribe(self):
        pass

    async def send_personal_message(self, user_id: ObjectId, message: str):
        if user_id in self.active_connections:
            for websocket in self.active_connections[user_id]:
                await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in chain(*[v for k, v in self.active_connections.items()]):
            await connection.send_text(message)


connection_manager = ConnectionManager()
