Absolutely. Below is a **proper GitHub-ready `README.md`** for your project. I’ve kept it technically accurate to what we actually built, without claiming features that aren't implemented.

````markdown
# Realtime Chatting Application

A backend-focused real-time chat application built with **FastAPI, WebSockets, PostgreSQL, SQLAlchemy, JWT authentication, and room-based messaging**.

The application demonstrates how to build a persistent and authenticated real-time communication backend with support for private messaging, offline message delivery, chat rooms, room membership, message history, pagination, authorization, and automated testing.

---

## 🚀 Features

### Authentication & Security

- User registration
- Secure password hashing using bcrypt
- User login
- JWT access-token authentication
- JWT-protected WebSocket connections
- Authentication for:
  - `/ws/chat`
  - `/ws/room`
  - `/ws/online`
- Authorization checks for room operations
- Protection against username spoofing through WebSocket query parameters
- Invalid/expired JWT rejection

### Private Chat

- Real-time one-to-one messaging
- Online user presence
- Offline message delivery
- Persistent private messages
- Message delivery tracking
- Private chat history
- Automatic delivery of pending messages when a user reconnects

### Room Chat

- Create/join rooms
- Leave rooms
- Persistent room membership
- Real-time room messaging
- Room member listing
- Persistent room messages
- Room message history
- Paginated room history
- Authorization based on room membership

### Reliability

- Connection management
- Detection and cleanup of disconnected WebSocket clients
- Safe message broadcasting
- Room connection management
- Persistent database-backed room membership
- Handling of offline users

### Testing

Automated tests using **pytest** covering:

- Password hashing
- Password verification
- JWT creation
- JWT validation
- Invalid JWT handling
- User registration
- User login
- Invalid login credentials
- Authenticated WebSocket connections
- Private messaging
- Offline message delivery
- Room connections
- Room joining
- Room messaging
- Room message persistence
- Room history
- Pagination
- Room authorization
- Invalid JWT WebSocket connections

**Current test status: 20 tests passing.**

---

# 🏗️ Architecture

```text
                         Client
                           │
                           │
                    REST / WebSocket
                           │
                           ▼
                    ┌─────────────┐
                    │   FastAPI   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        Authentication   WebSocket    REST APIs
              │            │
              │       ┌────┼────┐
              │       │    │    │
              │       ▼    ▼    ▼
              │     Chat Room Online
              │       │    │    │
              └───────┼────┼────┘
                      │
                      ▼
                 Authorization
                      │
                      ▼
              ┌───────────────┐
              │  SQLAlchemy   │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │  PostgreSQL   │
              │   / Supabase  │
              └───────────────┘
````

---

# 🔌 WebSocket Architecture

The application uses three separate WebSocket endpoints.

## 1. Personal Chat

```text
/ws/chat
```

Used for one-to-one private communication.

Authentication is performed using a JWT:

```text
ws://localhost:8000/ws/chat?token=<JWT>
```

The username is extracted from the JWT rather than being trusted from a client-provided username parameter.

---

## 2. Room Chat

```text
/ws/room
```

Used for room-based communication.

Example:

```text
ws://localhost:8000/ws/room?token=<JWT>
```

Users can:

* Join rooms
* Leave rooms
* Send room messages
* Request room history
* Request room members

Room operations are authorized using persistent room membership.

---

## 3. Online Presence

```text
/ws/online
```

Used for online-user presence updates.

Example:

```text
ws://localhost:8000/ws/online?token=<JWT>
```

The server maintains active presence connections and broadcasts the current online-user list.

---

# 🔐 Authentication Flow

Authentication uses JWT access tokens.

```text
                  Registration
                       │
                       ▼
                Password received
                       │
                       ▼
                 bcrypt hashing
                       │
                       ▼
                  PostgreSQL
                       │
                       │
                       ▼
                    Login
                       │
                       ▼
              Password verification
                       │
                       ▼
                 JWT generated
                       │
                       ▼
             WebSocket connection
                       │
                       ▼
                 JWT validation
                       │
                       ▼
             Username extracted
                       │
                       ▼
              Authenticated user
```

The application does not rely on:

```text
?username=ganesh
```

to establish the user's identity.

Instead:

```text
JWT
 │
 └── sub = username
```

is used to identify the authenticated user.

---

# 🛡️ Authorization

Authentication and authorization are handled separately.

### Authentication

Answers:

> Who is this user?

### Authorization

Answers:

> Is this user allowed to perform this operation?

For room operations, persistent membership is checked using the database.

For example:

```text
User
  │
  ▼
Room membership check
  │
  ├── Member
  │     └── Allow operation
  │
  └── Not a member
        └── Reject operation
```

The following room operations require membership:

* Room messaging
* Room history
* Room member listing

---

# 💾 Database Design

The application uses PostgreSQL through SQLAlchemy.

## Users

```text
users
├── id
├── username
├── password_hash
└── created_at
```

## Private Messages

```text
messages
├── id
├── sender
├── receiver
├── message
├── delivered
└── created_at
```

## Rooms

```text
rooms
├── id
├── name
└── created_at
```

## Room Members

```text
room_members
├── id
├── room_id
├── user_id
└── joined_at
```

## Room Messages

```text
room_messages
├── id
├── room_id
├── sender_id
├── message
└── created_at
```

### Relationship

```text
users
  │
  ├───────────────┐
  │               │
  ▼               ▼
messages      room_members
                  │
                  ▼
                rooms
                  │
                  ▼
            room_messages
```

---

# 🗂️ Project Structure

```text
Realtime_Chatting_Application/
│
├── auth/
│   ├── __init__.py
│   └── security.py
│
├── database/
│   ├── database.py
│   └── models.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_chat.py
│   └── test_rooms.py
│
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── ...
│
├── connectionManager.py
├── main.py
├── models.py
├── alembic.ini
├── .env
├── requirements.txt
└── README.md
```

---

# 🛠️ Technology Stack

| Technology  | Purpose                       |
| ----------- | ----------------------------- |
| Python      | Backend programming language  |
| FastAPI     | Web framework                 |
| WebSockets  | Real-time communication       |
| PostgreSQL  | Persistent database           |
| Supabase    | Hosted PostgreSQL             |
| SQLAlchemy  | ORM/database interaction      |
| Alembic     | Database migrations           |
| Pydantic    | Request/data validation       |
| Passlib     | Password hashing              |
| bcrypt      | Password hashing algorithm    |
| python-jose | JWT creation and verification |
| Uvicorn     | ASGI server                   |
| Pytest      | Automated testing             |
| Postman     | API and WebSocket testing     |

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone <your-repository-url>
```

Navigate into the project:

```bash
cd Realtime_Chatting_Application
```

---

## 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
```

Activate it:

```powershell
venv\Scripts\activate
```

---

## 3. Install dependencies

```powershell
pip install -r requirements.txt
```

If `requirements.txt` has not been generated yet:

```powershell
pip freeze > requirements.txt
```

---

# 🔑 Environment Configuration

Create a `.env` file in the project root.

```env
DATABASE_URL=your_postgresql_connection_string
```

Example format:

```env
DATABASE_URL=postgresql://username:password@host:5432/database
```

Do not commit `.env` to Git.

Add it to `.gitignore`:

```gitignore
.env
venv/
__pycache__/
.pytest_cache/
.idea/
```

---

# 🗄️ Database Setup

The application uses SQLAlchemy and Alembic for database management.

Check the current migration:

```powershell
alembic current
```

Generate a migration when the database model changes:

```powershell
alembic revision --autogenerate -m "description of change"
```

Apply migrations:

```powershell
alembic upgrade head
```

> For the POC, the database is hosted using PostgreSQL/Supabase.

---

# ▶️ Running the Application

Start the FastAPI server:

```powershell
uvicorn main:app --reload
```

The application will be available at:

```text
http://localhost:8000
```

FastAPI documentation:

```text
http://localhost:8000/docs
```

---

# 🔑 Authentication API

## Register

```http
POST /auth/register
```

Request:

```json
{
    "username": "ganesh",
    "password": "hello123"
}
```

Response:

```json
{
    "success": true,
    "message": "User registered successfully",
    "user": {
        "id": 1,
        "username": "ganesh"
    }
}
```

---

## Login

```http
POST /auth/login
```

Request:

```json
{
    "username": "ganesh",
    "password": "hello123"
}
```

Response:

```json
{
    "success": true,
    "message": "Login successful",
    "access_token": "<JWT>",
    "token_type": "bearer"
}
```

The returned JWT is used to authenticate WebSocket connections.

---

# 💬 Private Chat

Connect using:

```text
ws://localhost:8000/ws/chat?token=<JWT>
```

Send:

```json
{
    "to": "ashish",
    "message": "Hello Ashish"
}
```

The server identifies the sender from the JWT.

The client does not need to provide:

```json
{
    "from": "ganesh"
}
```

This prevents the client from choosing another user's identity.

---

# 👥 Room Chat

Connect:

```text
ws://localhost:8000/ws/room?token=<JWT>
```

## Join a room

```json
{
    "type": "join_room",
    "room": "developer"
}
```

## Send a room message

```json
{
    "type": "room_message",
    "room": "developer",
    "message": "Hello developers"
}
```

## Get room history

```json
{
    "type": "room_history",
    "room": "developer",
    "limit": 5,
    "offset": 0
}
```

Example response:

```json
{
    "type": "room_history",
    "room": "developer",
    "limit": 5,
    "offset": 0,
    "next_offset": 5,
    "has_more": true,
    "messages": [
        {
            "id": 1,
            "sender": "ganesh",
            "message": "Hello",
            "created_at": "..."
        }
    ]
}
```

## Get room members

```json
{
    "type": "get_room_members",
    "room": "developer"
}
```

Only users who are members of the room can access the room member list.

## Leave a room

```json
{
    "type": "leave_room",
    "room": "developer"
}
```

---

# 🟢 Online Presence

Connect:

```text
ws://localhost:8000/ws/online?token=<JWT>
```

The server maintains the online-user list and broadcasts presence updates.

Example:

```json
{
    "type": "online_users",
    "users": [
        "ganesh",
        "ashish"
    ]
}
```

---

# 📨 Offline Message Delivery

The application supports offline private messaging.

Example:

```text
Ganesh
   │
   │ sends message
   ▼
Ashish is offline
   │
   ▼
Message stored in PostgreSQL
   │
   ▼
Ashish connects
   │
   ▼
Pending message delivered
   │
   ▼
Message marked delivered
```

This allows messages to survive a user's temporary disconnection.

---

# 📜 Chat History

Private messages and room messages are persisted in PostgreSQL.

Room history supports pagination:

```json
{
    "type": "room_history",
    "room": "developer",
    "limit": 5,
    "offset": 0
}
```

Response metadata includes:

```text
limit
offset
next_offset
has_more
```

This prevents the server from returning an unnecessarily large history in a single response.

---

# 🧪 Testing

The project uses `pytest`.

Run the complete test suite:

```powershell
pytest -v
```

Current result:

```text
20 passed
```

Tests use an isolated test database rather than the application's real PostgreSQL database.

### Test categories

```text
Authentication
    ├── Password hashing
    ├── Password verification
    ├── JWT generation
    ├── JWT validation
    ├── Registration
    └── Login

Private Chat
    ├── WebSocket authentication
    ├── Private messaging
    └── Offline delivery

Rooms
    ├── WebSocket authentication
    ├── Joining
    ├── Messaging
    ├── Persistence
    ├── History
    ├── Pagination
    └── Authorization
```

---

# 🌐 External WebSocket Access

The application can be exposed outside the local network using a tunneling service.

For local development:

```text
ws://localhost:8000/ws/chat?token=<JWT>
```

For an externally exposed HTTPS/WSS endpoint, the tunnel provides the public address.

The exact tunnel provider and configuration are environment-specific.

---

# 🔒 Security Considerations

The current POC includes:

* bcrypt password hashing
* JWT authentication
* JWT-protected WebSockets
* Room membership authorization
* Invalid JWT rejection
* Database-backed authorization
* No client-controlled sender identity

For a full production deployment, additional hardening would be required, including:

* Secure secret management
* Strong randomly generated JWT secret
* HTTPS/WSS configuration
* Rate limiting
* Structured logging
* Monitoring and alerting
* Database backup/recovery
* Load/concurrency testing
* Multi-instance WebSocket coordination
* CI/CD
* Production deployment configuration

---

# 🚧 Current Scope

This project is intentionally focused on the **backend and real-time communication layer**.

There is currently no frontend application.

Clients can be tested using tools such as:

* Postman
* WebSocket clients
* REST clients

The project is intended as a **backend-focused real-time chat POC**.

---

# 🎯 Learning Objectives

This project demonstrates practical implementation of:

* FastAPI application development
* WebSocket communication
* Connection management
* Real-time message broadcasting
* Private messaging
* Room-based communication
* PostgreSQL persistence
* SQLAlchemy ORM
* Alembic migrations
* Authentication
* Password hashing
* JWT
* WebSocket authentication
* Authorization
* Offline message handling
* Pagination
* Automated testing
* Separation of runtime state and persistent state

---

# 📌 Project Status

**Status: POC Complete**

Core functionality has been implemented and tested.

```text
FastAPI                         ✅
WebSockets                      ✅
Private Chat                    ✅
Offline Messages                ✅
Online Presence                 ✅
Room Chat                       ✅
Persistent Room Membership      ✅
Room History                    ✅
Pagination                      ✅
PostgreSQL                      ✅
SQLAlchemy                      ✅
Alembic                         ✅
Authentication                  ✅
JWT                             ✅
Authorization                  ✅
Automated Tests                 ✅
20 Tests Passing                ✅
```

---

# 🔮 Future Improvements

Possible future enhancements include:

* Refresh tokens
* JWT secret management through environment variables
* Password reset
* Email verification
* User profile management
* Message deletion/editing
* Read receipts
* Typing indicators
* Message search
* Redis-based WebSocket coordination
* Horizontal scaling
* Rate limiting
* Structured logging
* Health-check endpoints
* Metrics and monitoring
* CI/CD pipeline
* Containerization with Docker
* Production cloud deployment
* Frontend client

---

# 👨‍💻 Author

**Ganesh Neela**

Backend-focused real-time chat application built using:

**FastAPI • WebSockets • PostgreSQL • SQLAlchemy • JWT • Pytest**

---

````

### One recommendation before putting this on GitHub

Your current README can be the **main project documentation**, but I would also add these two files:

```text
.gitignore
requirements.txt
````

And make sure your `.env` and JWT secret are **never committed**.

For the GitHub repository, the final structure should look roughly like:

```text
Realtime_Chatting_Application/
│
├── auth/
├── database/
├── tests/
├── alembic/
├── main.py
├── connectionManager.py
├── models.py
├── alembic.ini
├── requirements.txt
├── .gitignore
└── README.md
```

That gives you a clean, professional repository structure suitable for presenting the project as a **backend real-time systems POC**.
