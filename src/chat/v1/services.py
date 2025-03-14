from fastapi import WebSocket, HTTPException
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from .database import connection
from .models import User, Chat, Group, Message

import logging

logger = logging.getLogger(__name__)


async def get_or_create_group(group_name: str, user_name: str, session=None):
    query = select(Group).where(Group.name == group_name).options(joinedload(Group.members))
    result = await session.execute(query)
    group = result.scalars().first()
    if not group:
        group = Group(name=group_name, creator=user_name)
        session.add(group)
        await session.flush()
    return group


async def get_or_create_user(user_name: str, session=None):
    query = select(User).where(User.name == user_name)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        user = User(name=user_name)
        session.add(user)
        await session.flush()
    return user


async def get_or_create_chat(chatname: str, chattype: str, session=None):
    query = select(Chat).where(Chat.name == chatname).options(joinedload(Chat.messages))
    result = await session.execute(query)
    chat = result.scalars().first()
    if not chat:
        chat = Chat(name=chatname, type=chattype)
        session.add(chat)
        await session.flush()
    return chat


@connection
async def add_member(group_name: str, user_name: str, session=None) -> Group:
    user = await get_or_create_user(user_name, session=session)
    group = await get_or_create_group(group_name, user_name, session=session)

    await session.refresh(group, ["members"])
    if user not in group.members:
        group.members.append(user)
    await session.commit()
    return group


@connection
async def save_msg(chatname: str, chattype: str, username: str, read: bool, msg: str, session=None):
    chat = await get_or_create_chat(chatname, chattype, session=session)
    user = await get_or_create_user(username, session=session)
    message = Message(user_id=user.id, chat_id=chat.id, content=msg, read=read)
    session.add(message)
    await session.flush()
    await session.refresh(chat, ["messages"])
    chat.messages.append(message)
    await session.commit()


@connection
async def get_chat_history(chat_id, session=None):
    query = select(Chat).where(Chat.id == chat_id).options(joinedload(Chat.messages))
    rslt = await session.execute(query)
    chat = rslt.scalars().first()
    return chat.messages


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, chat_hash: str = None):
        await websocket.accept()
        self.active_connections[chat_hash].append(websocket)

    def disconnect(self, websocket: WebSocket, chat_hash: str = None):
        self.active_connections[chat_hash].remove(websocket)

    async def send_personal_message(self, websocket: WebSocket, message: str = None):
        await websocket.send_text(message)

    async def broadcast(self, websocket: WebSocket, message: str = None, chat_hash: str = None):
        for connection in self.active_connections[chat_hash]:
            if connection == websocket:
                continue
            await connection.send_text(message)

    async def is_active_user(self, chat_hash: str = None,) -> bool:
        connection = self.active_connections[chat_hash]
        if len(connection) == 2:
            return True
        elif len(connection) < 2:
            return False
        elif len(connection) > 2:
            raise HTTPException(status_code=500)

    async def is_active_group(self, chat_hash: str = None, group: Group = None) -> bool:
        connection = self.active_connections[chat_hash]
        online_members = len(connection)
        common_members = len(group.members)
        if common_members == online_members:
            return True
        return False
