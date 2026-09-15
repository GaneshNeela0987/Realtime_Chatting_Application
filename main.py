import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from connectionManager import ConnectionManager

manager = ConnectionManager()

app = FastAPI(
    docs_url="/docs"
)


@app.get("/")
async def home():
    return {"message": "Chat server is running"}


@app.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    username: str = Query(...)
):

    await manager.connect(websocket)

    print(f"{username} connected")

    try:
        while True:
            data = await websocket.receive_text()

            await manager.broadcast(
                f"{username}: {data}"
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"{username} disconnected")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
