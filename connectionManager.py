# from fastapi import WebSocket
#
#
# class ConnectionManager:
#     def __init__(self):
#         # self.active_connections: list[WebSocket] = [] # for broadcast channel, all the sockets will be in one single list and one message will go to all sockets, to fix this we can use dictionary
#         self.active_connections:dict[str,WebSocket] = {}  # for broadcast channel, all the sockets will be in one single list and one message will go to all sockets, to fix this we can use dictionary
#         self.online_connections:list[WebSocket] = []
#
#     async def connect(self, websocket: WebSocket, username: str):
#         await websocket.accept()
#         # self.active_connections.append(websocket) # for broadcast channel, all the sockets will be in one single list and one message will go to all sockets, to fix this we can use dictionary
#         if username in self.active_connections:
#             await websocket.send_json(
#                 {
#                     "type":"error",
#                     "message":f"Username '{username}' is already connected",
#                 }
#             )
#
#             await websocket.close()
#             return False
#
#         self.active_connections[username] = websocket
#         return True
#
#
#     def disconnect(self, websocket: WebSocket, username: str):
#         # self.active_connections.remove(websocket) # for broadcast channel, all the sockets will be in one single list and one message will go to all sockets, to fix this we can use dictionary
#         self.active_connections.pop(username, None)
#
#     async def broadcast(self, data: dict): # message:str
#         # for connection in self.active_connections:
#         #     await connection.send_text(message)
#
#         for username, connection in self.active_connections.items():
#             # await connection.send_text(message)
#             await connection.send_json(data)
#
#
#     async def send_personal_message(self, data:dict, username: str): #for individual channel, we can use dictionary to store the sockets with their usernames as keys
#         websocket = self.active_connections.get(username)
#
#         if websocket:
#             await websocket.send_json(data)
#             return True
#         return False
#
#     async def connect_online(
#         self,
#         websocket: WebSocket
#     ):
#
#         await websocket.accept()
#
#         self.online_connections.append(websocket)
#
#
#     def disconnect_online(
#         self,
#         websocket: WebSocket
#     ):
#
#         if websocket in self.online_connections:
#
#             self.online_connections.remove(websocket)
#
#     async def broadcast_presence(
#         self,
#     ):
#         users = list(self.active_connections.keys())
#
#         data = {
#             "type": "online_users",
#             "users": users
#         }
#
#         for connection in self.online_connections:
#
#             await connection.send_json(data)


from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:

    def __init__(self):

        # =================================================
        # PERSONAL CHAT CONNECTIONS
        # username -> WebSocket
        # =================================================

        self.active_connections: dict[str, WebSocket] = {}

        # =================================================
        # ONLINE / PRESENCE CONNECTIONS
        # =================================================

        self.online_connections: list[WebSocket] = []

        # =================================================
        # ROOM CONNECTIONS
        # username -> room WebSocket
        # =================================================

        self.room_connections: dict[str, WebSocket] = {}

        # =================================================
        # ROOMS
        # room -> set of usernames
        # =================================================

        self.rooms: dict[str, set[str]] = {}

    # =====================================================
    # PERSONAL CHAT
    # =====================================================

    async def connect(self,websocket: WebSocket,username: str):

        await websocket.accept()

        if username in self.active_connections:

            await websocket.send_json({
                "type": "error",
                "message": f"Username '{username}' is already connected"
            })

            await websocket.close()

            return False

        self.active_connections[username] = websocket

        return True

    def disconnect(self, username: str):

        self.active_connections.pop(username,None)

    # =====================================================
    # PERSONAL CHAT BROADCAST
    # =====================================================

    async def broadcast(self,data: dict):

        disconnected_users =[]

        for username, connection in self.active_connections.items():

            try:
                await connection.send_json(data)

            except WebSocketDisconnect:

                disconnected_users.append(username)

        for username in disconnected_users:
            self.active_connections.pop(username,None)

    # =====================================================
    # PERSONAL MESSAGE
    # =====================================================

    async def send_personal_message(self,data: dict,username: str):

        websocket = self.active_connections.get(username)

        if websocket:

            await websocket.send_json(data)

            return True

        return False

    # =====================================================
    # ONLINE / PRESENCE CONNECTIONS
    # =====================================================

    async def connect_online(self,websocket: WebSocket):

        await websocket.accept()

        self.online_connections.append(websocket)

    def disconnect_online(self,websocket: WebSocket):

        if websocket in self.online_connections:

            self.online_connections.remove(websocket)

    async def broadcast_presence(self):

        users = list(self.active_connections.keys())

        data = {
            "type": "online_users",
            "users": users
        }

        disconnected_connections = []

        for connection in list(self.online_connections):

            try:
                await connection.send_json(data)

            except WebSocketDisconnect:
                disconnected_connections.append(connection)

        # Remove dead presence connections
        for connection in disconnected_connections:
            if connection in self.online_connections:
                self.online_connections.remove(connection)

    # =====================================================
    # ROOM CONNECTIONS
    # =====================================================

    async def connect_room(self,websocket: WebSocket,username: str):

        await websocket.accept()
        if username in self.room_connections:

            await websocket.send_json({
                "type": "error",
                "message": (
                    f"User '{username}' "
                    "already has a room connection"
                )
            })

            await websocket.close()

            return False

        self.room_connections[username] = websocket

        return True

    def disconnect_room(self,username: str):

        self.room_connections.pop(username,None)

    # =====================================================
    # JOIN ROOM
    # =====================================================

    def join_room(self,username: str,room: str):

        if room not in self.rooms:

            self.rooms[room] = set()

        self.rooms[room].add(username)

    # =====================================================
    # LEAVE ROOM
    # =====================================================

    def leave_room(self,username: str,room: str):

        if room not in self.rooms:
            return False

        if username not in self.rooms[room]:
            return False

        self.rooms[room].remove(username)

        # Delete empty room
        if not self.rooms[room]:
            del self.rooms[room]

        return True

    # =====================================================
    # LEAVE ALL ROOMS
    # =====================================================

    def leave_all_rooms(self,username: str):

        rooms_left = []
        # Use list() because rooms may be deleted
        # while we are iterating
        for room in list(self.rooms.keys()):

            if username in self.rooms[room]:

                self.rooms[room].remove(
                    username
                )

                rooms_left.append(
                    room
                )

                # Delete empty room
                if not self.rooms[room]:

                    del self.rooms[room]

        return rooms_left

    # =====================================================
    # ROOM MEMBER NOTIFICATION
    # =====================================================

    async def notify_room_members(self,room: str,data: dict,exclude_username: str | None = None):

        if room not in self.rooms:
            return

        disconnected_users = []

        for username in self.rooms[room]:
            if username == exclude_username:
                continue


            websocket = self.room_connections.get(username)

            # No active room connection
            if not websocket:
                disconnected_users.append(username)
                continue

            try:
                await websocket.send_json(data)

            except WebSocketDisconnect:
                disconnected_users.append(username)

        for username in disconnected_users:

            self.room_connections.pop(
                username,
                None
            )

            if room in self.rooms:
                self.rooms[room].discard(
                    username
                )

        if room in self.rooms:

            if not self.rooms[room]:
                del self.rooms[room]

    # =====================================================
    # GET USER ROOMS
    # =====================================================

    def get_user_rooms(self,username: str):

        return [
            room
            for room, users in self.rooms.items()
            if username in users
        ]

    # =====================================================
    # BROADCAST TO ROOM
    # =====================================================

    async def broadcast_to_room(self,room: str,data: dict):

        if room not in self.rooms:
            return False

        disconnected_users = []

        users = self.rooms[room]

        for username in users:

            websocket = self.room_connections.get(username)

            if not websocket:
                disconnected_users.append(username)
                continue

            try:
                await websocket.send_json(data)

            except WebSocketDisconnect:
                disconnected_users.append(username)

        for username in disconnected_users:

            self.room_connections.pop(username,None)

            if room in self.rooms:
                self.rooms[room].discard(username)

        if room in self.rooms:
            if not self.rooms[room]:
                del self.rooms[room]

        return True

    # =====================================================
    # GET ROOM MEMBERS
    # =====================================================

    def get_room_members(self,room: str):

        if room not in self.rooms:
            return None

        return list(self.rooms[room])