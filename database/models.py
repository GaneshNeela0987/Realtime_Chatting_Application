from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func

from database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)

    sender = Column(String(50), nullable=False)
    receiver = Column(String(50), nullable=False)

    message = Column(Text, nullable=False)

    delivered = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer,primary_key=True,index=True)

    name = Column(String(100),unique=True,nullable=False,index=True)

    created_at = Column(DateTime(timezone=True),server_default=func.now())

class RoomMember(Base):
    __tablename__ = "room_members"

    id = Column(Integer,primary_key=True,index=True)

    room_id = Column(Integer,ForeignKey("rooms.id"),nullable=False)

    user_id = Column(Integer,ForeignKey("users.id"),nullable=False)

    joined_at = Column(DateTime(timezone=True),server_default=func.now())


class RoomMessage(Base):
    __tablename__ = "room_messages"

    id = Column(Integer, primary_key=True, index=True)

    room_id = Column(Integer,ForeignKey("rooms.id"),nullable=False)

    sender_id = Column(Integer,ForeignKey("users.id"),nullable=False)

    message = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True),server_default=func.now())