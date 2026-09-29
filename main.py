# import uvicorn
# from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
# from pydantic import ValidationError
# from connectionManager import ConnectionManager
# from models import ChatModel
#
# manager = ConnectionManager()
#
# app = FastAPI(
#     docs_url="/docs"
# )
#
#
# @app.get("/")
# async def home():
#     return {"message": "Chat server is running"}
#
#
# @app.websocket("/ws/chat")
# async def websocket_endpoint(
#         websocket: WebSocket,
#         username: str = Query(...)
# ):
#     # await manager.connect(websocket) # for broadcast channel, all the sockets will be in one single list and one message will go to all sockets, to fix this we can use dictionary
#     await manager.connect(websocket,
#                           username)  # for individual channel, we can use dictionary to store the sockets with their usernames as keys
#
#     print(f"{username} connected")
#
#     data = {
#         "type": "user_joined",
#         "message": f"{username} joined the chat"
#     }
#
#     await manager.broadcast(data) #
#
#     # await manager.broadcast_presence({
#     #     "type": "user_joined",
#     #     "username": username
#     # }) #broadcasting the presence of the user to all connected clients
#
#     await manager.broadcast_presence()
#
#     try:
#         while True:
#             data = await websocket.receive_json()
#             print(data)
#             try:
#                 chat_message = ChatModel(**data)
#
#             except ValidationError as e:
#                 await websocket.send_json({
#                     "type": "error",
#                     "message": "Invalid message format",
#                     "details": e.errors()
#                 })
#                 continue
#             recipient = chat_message.to
#             message = chat_message.message
#
#             sent = await manager.send_personal_message(
#                 {
#                     "type": "private_message",
#                     "from": username,
#                     "to": recipient,
#                     "message": message
#                 },
#                 recipient
#             )
#             if not sent:
#                 await websocket.send_json({
#                     "type": "error",
#                     "message": f"User '{recipient}' is not connected"
#                 })
#     except WebSocketDisconnect:
#         # manager.disconnect(websocket) # for broadcast channel, all the sockets will be in one single list and one message will go to all sockets, to fix this we can use dictionary
#         manager.disconnect(websocket, username)  # for individual channel, we can use dictionary to store
#
#         await manager.broadcast({
#             "type": "user_left",
#             "username": username
#         })
#
#         # await manager.broadcast_presence({
#         #     "type": "user_left",
#         #     "username": username
#         # })
#
#         await manager.broadcast_presence()
#         print(f"{username} disconnected")
#
#
# @app.websocket("/ws/online")
# async def online_users(websocket: WebSocket):
#
#     await manager.connect_online(websocket)
#
#     try:
#
#         users = list(manager.active_connections.keys())
#
#         await websocket.send_json({
#             "type": "online_users",
#             "users": users
#         })
#         while True:
#
#             await websocket.receive_text()
#
#     except WebSocketDisconnect:
#
#         manager.disconnect_online(websocket)
#
#         print("Online users client disconnected")
#
#
# # @app.websocket("/ws/chat/personal")
# # async def send_personal(message: str, username: str, websocket: WebSocket):
# #
# #     await manager.connect(websocket, username) # for individual channel, we can use dictionary to store the sockets with their usernames as keys
# #     await manager.send_personal_message(message, username)
# #
# #     print("connection established with " + username)
# #
# #     try:
# #         while True:
# #             data = await manager.active_connections[username].receive_json()
# #             print(f"{username}: {data}")
# #     except WebSocketDisconnect:
# #         manager.disconnect(manager.active_connections[username], username)
# #         print(f"{username} disconnected")
#
#
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)


import uvicorn

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Query
)

from pydantic import ValidationError

from connectionManager import ConnectionManager
from models import ChatModel
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session
from fastapi import Depends

from database.database import get_db
from database.models import User, Message

manager = ConnectionManager()


app = FastAPI(
    docs_url="/docs"
)


# =========================================================
# BASIC HTTP ENDPOINT
# =========================================================

@app.get("/")
async def home():

    return {
        "message": "Chat server is running"
    }


# =========================================================
# PERSONAL CHAT
# =========================================================

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket,username: str = Query(...),db: Session = Depends(get_db)):

    # -----------------------------------------------------
    # CONNECT USER
    # -----------------------------------------------------

    connected = await manager.connect(websocket,username)

    # Stop if duplicate username
    if not connected:
        return

    # Check whether user already exists
    result = db.execute(select(User).where(User.username == username))

    user = result.scalar_one_or_none()

    # Create user if this is the first connection
    if user is None:
        user = User(username=username)

        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"User '{username}' created in database")

    else:
        print(f"User '{username}' already exists in database")

    # Stop if duplicate username
    if not connected:
        return

    print(f"{username} connected")

    # -----------------------------------------------------
    # DELIVER PENDING MESSAGES
    # -----------------------------------------------------

    pending_query = select(Message).where(
        Message.receiver == username,
        Message.delivered == False
    ).order_by(Message.created_at.asc())

    pending_result = db.execute(pending_query)

    pending_messages = pending_result.scalars().all()

    for pending_message in pending_messages:

        sent = await manager.send_personal_message(
            {
                "type": "offline_message",
                "id": pending_message.id,
                "from": pending_message.sender,
                "to": pending_message.receiver,
                "message": pending_message.message,
                "created_at":
                    pending_message.created_at.isoformat()
                    if pending_message.created_at
                    else None
            },
            username
        )

        if sent:
            pending_message.delivered = True

    db.commit()
    # -----------------------------------------------------
    # USER JOINED
    # -----------------------------------------------------

    await manager.broadcast({
        "type": "user_joined",
        "message":
            f"{username} joined the chat"
    })

    # Update online users
    await manager.broadcast_presence()

    # -----------------------------------------------------
    # RECEIVE PERSONAL CHAT MESSAGES
    # -----------------------------------------------------

    try:

        while True:

            data = await websocket.receive_json()

            print(data)
            if data.get("type") == "chat_history":

                other_user = data.get("with")

                if not other_user:
                    await websocket.send_json({
                        "type": "error",
                        "message": "The 'with' field is required"
                    })
                    continue

                query = select(Message).where(
                    or_(
                        and_(
                            Message.sender == username,
                            Message.receiver == other_user
                        ),
                        and_(
                            Message.sender == other_user,
                            Message.receiver == username
                        )
                    )
                ).order_by(Message.created_at.asc())

                result = db.execute(query)

                messages = result.scalars().all()

                await websocket.send_json({
                    "type": "chat_history",
                    "with": other_user,
                    "messages": [
                        {
                            "id": msg.id,
                            "sender": msg.sender,
                            "receiver": msg.receiver,
                            "message": msg.message,
                            "created_at": msg.created_at.isoformat()
                            if msg.created_at else None
                        }
                        for msg in messages
                    ]
                })

                continue

            # -------------------------------------------------
            # VALIDATE MESSAGE
            # -------------------------------------------------

            try:

                chat_message = ChatModel(**data)

            except ValidationError as e:

                await websocket.send_json({
                    "type": "error",
                    "message":
                        "Invalid message format",
                    "details":
                        e.errors()
                })

                continue

            # -------------------------------------------------
            # EXTRACT MESSAGE
            # -------------------------------------------------

            recipient = chat_message.to

            message = chat_message.message

            # # -------------------------------------------------
            # # SEND PRIVATE MESSAGE
            # # -------------------------------------------------
            #
            # #Save to the DB
            # new_message = Message(
            #     sender=username,
            #     receiver=recipient,
            #     message=message
            # )
            # db.add(new_message)
            # db.commit()
            # db.refresh(new_message)
            #
            # #send to websocket
            # sent = await manager.send_personal_message(
            #     {
            #         "type":"private_message",
            #         "from":username,
            #         "to":recipient,
            #         "message":message
            #     },
            #     recipient)
            #
            # # -------------------------------------------------
            # # RECIPIENT NOT CONNECTED
            # # -------------------------------------------------
            #
            # if not sent:
            #     await websocket.send_json({
            #         "type":
            #             "error",
            #         "message":
            #             f"User '{recipient}' is not connected"
            #     })
            # -------------------------------------------------
            # CHECK WHETHER RECIPIENT EXISTS
            # -------------------------------------------------

            result = db.execute(
                select(User).where(User.username == recipient)
            )

            recipient_user = result.scalar_one_or_none()

            if recipient_user is None:
                await websocket.send_json({
                    "type": "error",
                    "message": f"User '{recipient}' does not exist"
                })

                continue

            # -------------------------------------------------
            # CHECK WHETHER RECIPIENT IS ONLINE
            # -------------------------------------------------

            recipient_online = recipient in manager.active_connections

            # -------------------------------------------------
            # SAVE MESSAGE
            # -------------------------------------------------

            new_message = Message(
                sender=username,
                receiver=recipient,
                message=message,
                delivered=False
            )

            db.add(new_message)
            db.commit()
            db.refresh(new_message)

            # -------------------------------------------------
            # RECIPIENT ONLINE
            # -------------------------------------------------

            if recipient_online:

                sent = await manager.send_personal_message(
                    {
                        "type": "private_message",
                        "id": new_message.id,
                        "from": username,
                        "to": recipient,
                        "message": message
                    },
                    recipient
                )

                if sent:
                    new_message.delivered = True

                    db.commit()

            else:

                # Recipient is offline.
                # Message remains delivered=False.

                await websocket.send_json({
                    "type": "message_queued",
                    "message":
                        f"User '{recipient}' is offline. "
                        "Message saved for delivery."
                })

            # # -------------------------------------------------
            # # CHECK WHETHER RECIPIENT IS CONNECTED
            # # -------------------------------------------------
            #
            # if recipient not in manager.active_connections:
            #     await websocket.send_json({
            #         "type": "error",
            #         "message": f"User '{recipient}' is not connected"
            #     })
            #
            #     continue
            #
            # # -------------------------------------------------
            # # SAVE MESSAGE TO DATABASE
            # # -------------------------------------------------
            #
            # new_message = Message(
            #     sender=username,
            #     receiver=recipient,
            #     message=message
            # )
            #
            # db.add(new_message)
            # db.commit()
            # db.refresh(new_message)
            #
            # # -------------------------------------------------
            # # SEND PRIVATE MESSAGE
            # # -------------------------------------------------
            #
            # sent = await manager.send_personal_message(
            #     {
            #         "type": "private_message",
            #         "from": username,
            #         "to": recipient,
            #         "message": message
            #     },
            #     recipient
            # )
    # -----------------------------------------------------
    # USER DISCONNECTED
    # -----------------------------------------------------

    except WebSocketDisconnect:

        manager.disconnect(username)

        # Notify personal-chat clients
        await manager.broadcast({
            "type":
                "user_left",
            "username":
                username
        })

        # Update online users
        await manager.broadcast_presence()

        print(f"{username} disconnected")


# =========================================================
# ONLINE USERS
# =========================================================

@app.websocket("/ws/online")
async def online_users(
    websocket: WebSocket
):

    # Register presence connection
    await manager.connect_online(websocket)

    try:

        # Send current online users
        users = list(manager.active_connections.keys())

        await websocket.send_json({
            "type":"online_users",
            "users":users
        })

        # Keep connection alive
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:

        manager.disconnect_online(websocket)

        print("Online users client disconnected")


# =========================================================
# ROOM CHAT
# =========================================================

@app.websocket("/ws/room")
async def room_websocket(websocket: WebSocket,username: str = Query(...)):

    # -----------------------------------------------------
    # CONNECT ROOM SOCKET
    # -----------------------------------------------------
    connected = await manager.connect_room(websocket,username)

    if not connected:
        return

    print(f"{username} connected to room server")

    try:

        while True:

            data = await websocket.receive_json()
            message_type = data.get("type")

            # ---------------------------------------------
            # JOIN ROOM
            # ---------------------------------------------

            if message_type == "join_room":
                room = data.get("room")
                # Room name required
                if not room:
                    await websocket.send_json({
                        "type":"error",
                        "message":"Room name is required"
                    })
                    continue

                # Add user to room
                manager.join_room(username,room)

                # Confirm room join
                await websocket.send_json({
                    "type":"room_joined",
                    "username":username,
                    "room":room
                })

                await manager.notify_room_members(
                    room,
                    {
                        "type":"user_joined_room",
                        "username":username,
                        "room":room
                    },
                    exclude_username=username
                )

                continue

            # ---------------------------------------------
            # LEAVE ROOM
            # ---------------------------------------------

            if message_type == "leave_room":
                room = data.get("room")
                if not room:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Room name is required"
                    })
                    continue
                if room not in manager.rooms:
                    await websocket.send_json({
                        "type":"error",
                        "message":f"Room '{room}' ""does not exist"
                    })
                    continue


                if username not in manager.rooms[room]:

                    await websocket.send_json({
                        "type":"error",
                        "message":f"User '{username}' "f"is not a member of '{room}'"
                    })
                    continue

                await manager.notify_room_members(
                    room,
                    {
                        "type":"user_left_room",
                        "username":username,
                        "room":room
                    },
                    exclude_username=username
                )

                manager.leave_room(username,room)

                await websocket.send_json({
                    "type": "room_left",
                    "username": username,
                    "room": room
                })

                continue

            # ---------------------------------------------
            # ROOM MESSAGE
            # ---------------------------------------------

            if message_type == "room_message":
                room = data.get("room")
                message = data.get("message")

                # Validate room
                if not room:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Room name is required"
                    })
                    continue

                # Validate message
                if not message:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Message is required"
                    })
                    continue

                # Check whether user belongs to room
                if room not in manager.rooms:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Room '{room}' does not exist"
                    })

                    continue

                if username not in manager.rooms[room]:
                    await websocket.send_json({
                        "type": "error",
                        "message": (
                            f"User '{username}' "
                            f"is not a member of '{room}'"
                        )
                    })
                    continue

                # Broadcast message
                await manager.broadcast_to_room(
                    room,
                    {
                        "type": "room_message",
                        "room": room,
                        "from": username,
                        "message": message
                    }
                )
                continue

            # =================================================
            # GET ROOM MEMBERS
            # =================================================

            if message_type == "get_room_members":
                room = data.get("room")

                if not room:
                    await websocket.send_json({
                        "type":"error",
                        "message":"Room name is required"
                    })
                    continue

                # -------------------------------------------------
                # CHECK ROOM EXISTS
                # -------------------------------------------------

                members = manager.get_room_members(room)

                if members is None:
                    await websocket.send_json({
                        "type":"error",
                        "message":f"Room '{room}' does not exist"
                    })
                    continue

                # -------------------------------------------------
                # SEND MEMBERS
                # -------------------------------------------------

                await websocket.send_json({
                    "type":"room_members",
                    "room":room,
                    "members":members
                })
                continue

            # ---------------------------------------------
            # UNKNOWN MESSAGE TYPE
            # ---------------------------------------------

            await websocket.send_json({
                "type": "error",
                "message": "Unknown room message type"
            })

            continue


    except WebSocketDisconnect:
        # Get rooms before removing the user
        rooms_left = manager.get_user_rooms(username)

        # Notify remaining members
        for room in rooms_left:
            await manager.notify_room_members(
                room,
                {
                    "type": "user_left_room",
                    "username": username,
                    "room": room
                },
                exclude_username=username
            )

        # Remove room WebSocket connection
        manager.disconnect_room(username)

        # Remove user from every room
        manager.leave_all_rooms(username)

        print(
            f"{username} disconnected "
            f"from room server"
        )

        print(
            f"{username} removed from rooms: "
            f"{rooms_left}"
        )



# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    uvicorn.run(app,host="0.0.0.0",port=8000)
