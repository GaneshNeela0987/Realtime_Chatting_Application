from sqlalchemy import Column, Integer, String, Text, DateTime
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

    created_at = Column(DateTime(timezone=True), server_default=func.now())