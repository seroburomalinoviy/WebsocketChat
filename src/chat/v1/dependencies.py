from fastapi import HTTPException
import logging


logger = logging.getLogger(__name__)


async def is_chattype(chattype: str):
    if chattype == "private" or chattype == "public":
        return chattype
    raise HTTPException(status_code=422)
