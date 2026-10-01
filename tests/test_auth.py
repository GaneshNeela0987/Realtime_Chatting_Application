from auth.security import (hash_password,verify_password,create_access_token,verify_access_token)

def test_password_hashing():
    password = "hello123"

    hashed_password = hash_password(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password)
    assert not verify_password("wrongpassword", hashed_password)




def test_jwt_token():

    username = "ganesh"

    token = create_access_token(username)

    assert token is not None
    assert isinstance(token, str)

    decoded_username = verify_access_token(token)

    assert decoded_username == username


def test_invalid_jwt():

    invalid_token = "this-is-not-a-valid-jwt"

    username = verify_access_token(invalid_token)

    assert username is None


def test_register_user(client):

    response = client.post(
        "/auth/register",
        json={
            "username": "pytest_user",
            "password": "test123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["message"] == "User registered successfully"
    assert data["user"]["username"] == "pytest_user"

def test_login_user(client):

    # Register
    register_response = client.post(
        "/auth/register",
        json={
            "username": "login_test_user",
            "password": "test123"
        }
    )

    assert register_response.status_code == 200

    # Login
    login_response = client.post(
        "/auth/login",
        json={
            "username": "login_test_user",
            "password": "test123"
        }
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert data["success"] is True
    assert data["message"] == "Login successful"
    assert data["token_type"] == "bearer"
    assert data["access_token"]


def test_login_wrong_password(client):

    client.post(
        "/auth/register",
        json={
            "username": "wrong_password_user",
            "password": "correct123"
        }
    )

    response = client.post(
        "/auth/login",
        json={
            "username": "wrong_password_user",
            "password": "wrong123"
        }
    )

    data = response.json()

    assert data["success"] is False
    assert data["message"] == "Invalid username or password"