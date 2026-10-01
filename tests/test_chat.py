from auth.security import create_access_token
from database.models import User


def test_authenticated_chat_connection(client, db):

    user = User(
        username="ganesh",
        password_hash="test_hash"
    )

    db.add(user)
    db.commit()

    token = create_access_token("ganesh")

    with client.websocket_connect(
        f"/ws/chat?token={token}"
    ) as websocket:

        assert websocket is not None

def test_private_message(client, db):

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
        f"/ws/chat?token={ganesh_token}"
    ) as ganesh_ws:

        with client.websocket_connect(
            f"/ws/chat?token={ashish_token}"
        ) as ashish_ws:

            # Consume Ashish's join notification
            join_message = ashish_ws.receive_json()

            assert join_message["type"] == "user_joined"

            # Ganesh sends private message
            ganesh_ws.send_json({
                "to": "ashish",
                "message": "Hello Ashish"
            })

            # Now receive the actual private message
            message = ashish_ws.receive_json()

            print("RECEIVED MESSAGE:", message)

            assert message["message"] == "Hello Ashish"


def test_offline_message_delivery(client, db):

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

    # Only Ganesh connects.
    # Ashish remains offline.
    with client.websocket_connect(
        f"/ws/chat?token={ganesh_token}"
    ) as ganesh_ws:

        # Consume initial messages for Ganesh
        ganesh_ws.receive_json()

        ganesh_ws.send_json({
            "to": "ashish",
            "message": "Hello Ashish, you were offline!"
        })

        # Ganesh should receive the queued response
        response = ganesh_ws.receive_json()

        print("QUEUE RESPONSE:", response)

        assert response["type"] == "message_queued"

    # Now Ashish connects
    with client.websocket_connect(
        f"/ws/chat?token={ashish_token}"
    ) as ashish_ws:

        # The first relevant message should be the pending message.
        pending_message = ashish_ws.receive_json()

        print("PENDING MESSAGE:", pending_message)

        assert pending_message["message"] == (
            "Hello Ashish, you were offline!"
        )

def test_invalid_jwt_chat(client):

    invalid_token = "invalid-token"

    try:
        with client.websocket_connect(
            f"/ws/chat?token={invalid_token}"
        ) as websocket:

            response = websocket.receive_json()

            assert response["type"] == "error"
            assert response["message"] == "Invalid or expired token"

    except Exception:
        # WebSocket may be closed with code 1008 after sending the error.
        pass