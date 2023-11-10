from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect, status

from _documents.users.schema import UserList
from _documents.users.service import user_service
from _services.websocket.service import connection_manager as manager
from utils.guard import RoleGuard
from utils.logger import logger

stream_app = FastAPI()

def startup_stream():
    pass

@stream_app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user: UserList = Depends(user_service.parse_token_query)):
    if user is None: 
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await manager.connect(user, websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user, websocket)
