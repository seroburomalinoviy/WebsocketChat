from fastapi import FastAPI
from src.chat.v1.router import router
import logging

logging.basicConfig(level=logging.INFO)


app = FastAPI()

app.include_router(router)

