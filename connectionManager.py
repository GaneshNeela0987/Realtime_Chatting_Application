from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # self.active_connections: list[WebSocket] = [] # for broadcast channel, all the sockets will be in one single list and one message will go to all sockets, to fix this we can use dictionary
        self.active_connections:dict[str,WebSocket] = {}  # for broadcast channel, all the sockets will be in one single list and one message will go to all sockets, to fix this we can use dictionary

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        # self.active_connections.append(websocket) # for broadcast channel, all the sockets will be in one single list and one message will go to all sockets, to fix this we can use dictionary
        if username in self.active_connections:
            await websocket.send_json(
                {
                    "type":"error",
                    "message":f"Username '{username}' is already connected",
                }
            )

            await websocket.close()
            return False

        self.active_connections[username] = websocket
        return True


    def disconnect(self, websocket: WebSocket, username: str):
        # self.active_connections.remove(websocket) # for broadcast channel, all the sockets will be in one single list and one message will go to all sockets, to fix this we can use dictionary
        self.active_connections.pop(username, None)

    async def broadcast(self, data: dict): # message:str
        # for connection in self.active_connections:
        #     await connection.send_text(message)

        for username, connection in self.active_connections.items():
            # await connection.send_text(message)
            await connection.send_json(data)


    async def send_personal_message(self, data:dict, username: str): #for individual channel, we can use dictionary to store the sockets with their usernames as keys
        websocket = self.active_connections.get(username)

        if websocket:
            await websocket.send_json(data)
            return True
        return False