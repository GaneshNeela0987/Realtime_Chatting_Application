import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from pydantic import ValidationError
from connectionManager import ConnectionManager
from models import ChatModel

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
    # await manager.connect(websocket) # for broadcast channel, all the sockets will be in one single list and one message will go to all sockets, to fix this we can use dictionary
    await manager.connect(websocket,
                          username)  # for individual channel, we can use dictionary to store the sockets with their usernames as keys

    print(f"{username} connected")

    data = {
        "type": "user_joined",
        "message": f"{username} joined the chat"
    }

    await manager.broadcast(data)

    try:
        while True:
            data = await websocket.receive_json()
            print(data)
            try:
                chat_message = ChatModel(**data)

            except ValidationError as e:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid message format",
                    "details": e.errors()
                })
                continue
            recipient = chat_message.to
            message = chat_message.message

            sent = await manager.send_personal_message(
                {
                    "type": "private_message",
                    "from": username,
                    "to": recipient,
                    "message": message
                },
                recipient
            )
            if not sent:
                await websocket.send_text(f"User {recipient} is not connected.")

    except WebSocketDisconnect:
        # manager.disconnect(websocket) # for broadcast channel, all the sockets will be in one single list and one message will go to all sockets, to fix this we can use dictionary
        manager.disconnect(websocket, username)  # for individual channel, we can use dictionary to store
        print(f"{username} disconnected")


@app.websocket("/ws/online")
async def online_users(websocket: WebSocket):

    await websocket.accept()

    try:

        while True:

            await websocket.receive_text()

            users = list(manager.active_connections.keys())

            await websocket.send_json({
                "type": "online_users",
                "users": users
            })

    except WebSocketDisconnect:
        print("Online users client disconnected")


# @app.websocket("/ws/chat/personal")
# async def send_personal(message: str, username: str, websocket: WebSocket):
#
#     await manager.connect(websocket, username) # for individual channel, we can use dictionary to store the sockets with their usernames as keys
#     await manager.send_personal_message(message, username)
#
#     print("connection established with " + username)
#
#     try:
#         while True:
#             data = await manager.active_connections[username].receive_json()
#             print(f"{username}: {data}")
#     except WebSocketDisconnect:
#         manager.disconnect(manager.active_connections[username], username)
#         print(f"{username} disconnected")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
