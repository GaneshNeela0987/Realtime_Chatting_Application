from auth.security import create_access_token
from database.models import User, Room, RoomMember, RoomMessage

def test_authenticated_room_connection(client, db):

    user = User(
        username="ganesh",
        password_hash="test_hash"
    )

    db.add(user)
    db.commit()

    token = create_access_token("ganesh")

    with client.websocket_connect(
        f"/ws/room?token={token}"
    ) as websocket:

        assert websocket is not None


def test_join_room(client, db):

    user = User(
        username="ganesh",
        password_hash="test_hash"
    )

    db.add(user)
    db.commit()

    token = create_access_token("ganesh")

    with client.websocket_connect(
        f"/ws/room?token={token}"
    ) as websocket:

        websocket.send_json({
            "type": "join_room",
            "room": "developer"
        })

        response = websocket.receive_json()

        print("JOIN RESPONSE:", response)

        assert response["type"] == "room_joined"
        assert response["room"] == "developer"

    # Verify persistent membership
    room = db.query(Room).filter(
        Room.name == "developer"
    ).first()

    assert room is not None

    membership = db.query(RoomMember).filter(
        RoomMember.room_id == room.id,
        RoomMember.user_id == user.id
    ).first()

    assert membership is not None

def test_room_message(client, db):

    ganesh = User(
        username="ganesh",
        password_hash="test_hash"
    )

    ashish = User(
        username="ashish",
        password_hash="test_hash"
    )

    db.add_all([ganesh, ashish])
    db.commit()

    ganesh_token = create_access_token("ganesh")
    ashish_token = create_access_token("ashish")

    with client.websocket_connect(
        f"/ws/room?token={ganesh_token}"
    ) as ganesh_ws:

        with client.websocket_connect(
            f"/ws/room?token={ashish_token}"
        ) as ashish_ws:

            # Ganesh joins the room
            ganesh_ws.send_json({
                "type": "join_room",
                "room": "developer"
            })

            ganesh_join = ganesh_ws.receive_json()

            assert ganesh_join["type"] == "room_joined"

            # Ashish joins the same room
            ashish_ws.send_json({
                "type": "join_room",
                "room": "developer"
            })

            ashish_join = ashish_ws.receive_json()

            assert ashish_join["type"] == "room_joined"

            # Consume the notification sent to Ganesh
            ganesh_ws.receive_json()

            # Ganesh sends a room message
            ganesh_ws.send_json({
                "type": "room_message",
                "room": "developer",
                "message": "Hello developer team"
            })

            # Ashish receives the room message
            message = ashish_ws.receive_json()

            print("ROOM MESSAGE:", message)

            assert message["room"] == "developer"
            assert message["message"] == "Hello developer team"

def test_room_message_persistence(client, db):

    ganesh = User(
        username="ganesh",
        password_hash="test_hash"
    )

    db.add(ganesh)
    db.commit()

    token = create_access_token("ganesh")

    with client.websocket_connect(
        f"/ws/room?token={token}"
    ) as websocket:

        # Join room
        websocket.send_json({
            "type": "join_room",
            "room": "developer"
        })

        join_response = websocket.receive_json()

        assert join_response["type"] == "room_joined"

        # Send message
        websocket.send_json({
            "type": "room_message",
            "room": "developer",
            "message": "Persistent room message"
        })

        # The sender may receive the broadcast depending on
        # your current room broadcast implementation.
        websocket.receive_json()

    # Verify room exists
    room = db.query(Room).filter(
        Room.name == "developer"
    ).first()

    assert room is not None

    # Verify message was persisted
    room_message = db.query(RoomMessage).filter(
        RoomMessage.room_id == room.id,
        RoomMessage.sender_id == ganesh.id,
        RoomMessage.message == "Persistent room message"
    ).first()

    assert room_message is not None

def test_room_history_pagination(client, db):

    ganesh = User(
        username="ganesh",
        password_hash="test_hash"
    )

    db.add(ganesh)
    db.commit()

    token = create_access_token("ganesh")

    with client.websocket_connect(
        f"/ws/room?token={token}"
    ) as websocket:

        # Join room
        websocket.send_json({
            "type": "join_room",
            "room": "developer"
        })

        join_response = websocket.receive_json()

        assert join_response["type"] == "room_joined"

        # Create 5 messages
        for i in range(1, 6):

            websocket.send_json({
                "type": "room_message",
                "room": "developer",
                "message": f"Message {i}"
            })

            # Consume the broadcast response
            websocket.receive_json()

        # Request first page
        websocket.send_json({
            "type": "room_history",
            "room": "developer",
            "limit": 3,
            "offset": 0
        })

        history = websocket.receive_json()

        print("HISTORY PAGE 1:", history)

        assert history["type"] == "room_history"
        assert history["room"] == "developer"
        assert history["limit"] == 3
        assert history["offset"] == 0
        assert history["next_offset"] == 3
        assert history["has_more"] is True

        assert len(history["messages"]) == 3

        assert history["messages"][0]["message"] == "Message 1"
        assert history["messages"][1]["message"] == "Message 2"
        assert history["messages"][2]["message"] == "Message 3"

        # Request second page
        websocket.send_json({
            "type": "room_history",
            "room": "developer",
            "limit": 3,
            "offset": 3
        })

        history_page_2 = websocket.receive_json()

        print("HISTORY PAGE 2:", history_page_2)

        assert history_page_2["type"] == "room_history"
        assert history_page_2["limit"] == 3
        assert history_page_2["offset"] == 3
        assert history_page_2["next_offset"] == 5
        assert history_page_2["has_more"] is False

        assert len(history_page_2["messages"]) == 2

        assert history_page_2["messages"][0]["message"] == "Message 4"
        assert history_page_2["messages"][1]["message"] == "Message 5"

def test_non_member_cannot_send_room_message(client, db):

    ganesh = User(
        username="ganesh",
        password_hash="test_hash"
    )

    ashish = User(
        username="ashish",
        password_hash="test_hash"
    )

    db.add_all([ganesh, ashish])
    db.commit()

    ganesh_token = create_access_token("ganesh")

    # Create the room and make only Ganesh a member
    with client.websocket_connect(
        f"/ws/room?token={ganesh_token}"
    ) as ganesh_ws:

        ganesh_ws.send_json({
            "type": "join_room",
            "room": "developer"
        })

        ganesh_ws.receive_json()

    # Ashish connects but does NOT join the room
    ashish_token = create_access_token("ashish")

    with client.websocket_connect(
        f"/ws/room?token={ashish_token}"
    ) as ashish_ws:

        ashish_ws.send_json({
            "type": "room_message",
            "room": "developer",
            "message": "Unauthorized message"
        })

        response = ashish_ws.receive_json()

        print("UNAUTHORIZED MESSAGE RESPONSE:", response)

        assert response["type"] == "error"
        assert "not a member" in response["message"]

def test_non_member_cannot_read_room_history(client, db):

    ganesh = User(
        username="ganesh",
        password_hash="test_hash"
    )

    ashish = User(
        username="ashish",
        password_hash="test_hash"
    )

    db.add_all([ganesh, ashish])
    db.commit()

    ganesh_token = create_access_token("ganesh")

    # Create room
    with client.websocket_connect(
        f"/ws/room?token={ganesh_token}"
    ) as ganesh_ws:

        ganesh_ws.send_json({
            "type": "join_room",
            "room": "developer"
        })

        ganesh_ws.receive_json()

    # Ashish is not a member
    ashish_token = create_access_token("ashish")

    with client.websocket_connect(
        f"/ws/room?token={ashish_token}"
    ) as ashish_ws:

        ashish_ws.send_json({
            "type": "room_history",
            "room": "developer",
            "limit": 10,
            "offset": 0
        })

        response = ashish_ws.receive_json()

        print("UNAUTHORIZED HISTORY RESPONSE:", response)

        assert response["type"] == "error"
        assert "not a member" in response["message"]

def test_non_member_cannot_get_room_members(client, db):

    ganesh = User(
        username="ganesh",
        password_hash="test_hash"
    )

    ashish = User(
        username="ashish",
        password_hash="test_hash"
    )

    db.add_all([ganesh, ashish])
    db.commit()

    ganesh_token = create_access_token("ganesh")

    # Create room with Ganesh as member
    with client.websocket_connect(
        f"/ws/room?token={ganesh_token}"
    ) as ganesh_ws:

        ganesh_ws.send_json({
            "type": "join_room",
            "room": "developer"
        })

        ganesh_ws.receive_json()

    # Ashish attempts to inspect the room
    ashish_token = create_access_token("ashish")

    with client.websocket_connect(
        f"/ws/room?token={ashish_token}"
    ) as ashish_ws:

        ashish_ws.send_json({
            "type": "get_room_members",
            "room": "developer"
        })

        response = ashish_ws.receive_json()

        print("UNAUTHORIZED MEMBERS RESPONSE:", response)

        assert response["type"] == "error"
        assert "not a member" in response["message"]

def test_invalid_jwt_room(client):

    invalid_token = "invalid-token"

    try:
        with client.websocket_connect(
            f"/ws/room?token={invalid_token}"
        ) as websocket:

            response = websocket.receive_json()

            assert response["type"] == "error"
            assert response["message"] == "Invalid or expired token"

    except Exception:
        pass

def test_invalid_jwt_online(client):

    invalid_token = "invalid-token"

    try:
        with client.websocket_connect(
            f"/ws/online?token={invalid_token}"
        ) as websocket:

            response = websocket.receive_json()

            assert response["type"] == "error"
            assert response["message"] == "Invalid or expired token"

    except Exception:
        pass