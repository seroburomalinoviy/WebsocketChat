from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, text, Enum, Table, Column, Boolean

from .database import Base

import enum


user_group_table = Table(
    "user_group_table",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("group_id", ForeignKey("groups.id"), primary_key=True),
)

user_message_table = Table(
    "user_message_table",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("message_id", ForeignKey("messages.id"), primary_key=True),
    Column("chat_id", ForeignKey("chats.id")),
    Column("read", Boolean, nullable=True, default=False, server_default="False"),
)


class ChatType(str, enum.Enum):
    public = "Общий"
    private = "Личный"


class User(Base):
    name: Mapped[str] = mapped_column(String(20), unique=True)
    email: Mapped[str] = mapped_column(String(30), nullable=True)
    password: Mapped[str] = mapped_column(String(30), nullable=True)

    messages: Mapped[list["Message"]] = relationship(
        "Message",
        secondary=user_message_table,
        back_populates="users"
    )

    groups: Mapped[list["Group"]] = relationship(
        "Group",
        secondary=user_group_table,
        back_populates="members"
        # cascade="all, delete-orphan"
    )


class Chat(Base):
    name: Mapped[str] = mapped_column(String(30), unique=True)
    type: Mapped[ChatType] = mapped_column(
        Enum(ChatType, name="chatttype"),
        default=ChatType.private,
        server_default="private"
    )

    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
    )


class Message(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"))
    content: Mapped[str] = mapped_column(String(100))
    read: Mapped[bool] = mapped_column(Boolean, default=False, server_default="False", nullable=True)

    users: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_message_table,
        back_populates="messages"
    )
    chat: Mapped["Chat"] = relationship(
        "Chat",
        back_populates="messages"
    )


class Group(Base):
    name: Mapped[str] = mapped_column(String(20))
    creator: Mapped[str] = mapped_column(String(20))

    members: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_group_table,
        back_populates="groups",
    )




