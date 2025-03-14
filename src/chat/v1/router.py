from fastapi import APIRouter, Depends, WebSocket
from fastapi.responses import HTMLResponse
import logging
from starlette.websockets import WebSocketDisconnect

from .config import get_settings
from .services import ConnectionManager, save_msg, add_member, get_chat_history
from .dependencies import is_chattype
from .utils import hash_of_names

settings = get_settings()
logger = logging.getLogger(__name__)
router = APIRouter()
index_page = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
        <style>
            body {
                background-color: black;
                color: white;
                font-family: Arial, sans-serif;
            }
            input, button {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                padding: 5px;
            }
            button:hover {
                background-color: #555;
            }
            ul {
                list-style-type: none;
                padding: 0;
            }
            li {
                background-color: #222;
                padding: 5px;
                margin: 5px 0;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <label>Chat name: <input type="text" id="chatname" autocomplete="off" value=""/></label>
            <label>Select chat type (private / public): <input type="text" id="chattype" autocomplete="off" value="private"/></label>
            <label>Your name: <input type="text" id="username" autocomplete="off" value="bar"/></label>
            <button onclick="connect(event)">Connect</button>
            <button onclick="disconnect(event)">Disconnect</button>
            <hr>
            <label>Message: <input type="text" id="messageText" autocomplete="off"/></label>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
        var ws = null;
            function connect(event) {
                var chat_name = document.getElementById("chatname");
                var user_name = document.getElementById("username");
                var chat_type = document.getElementById("chattype");
                ws = new WebSocket("ws://localhost:8000/chat/" + chat_type.value + "/" + chat_name.value + "/" + user_name.value);
                ws.onmessage = function(event) {
                    var messages = document.getElementById('messages');
                    var message = document.createElement('li');
                    var content = document.createTextNode(event.data);
                    message.appendChild(content);
                    messages.appendChild(message);
                };
                event.preventDefault();
            }
            
            function disconnect(event) {
                if (ws) {
                    var user_name = document.getElementById("username").value;
                    ws.send(JSON.stringify({ type: "disconnect", user: user_name }));
                    ws.close();
                    ws = null;
                }
                event.preventDefault();
            }
            
            function sendMessage(event) {
                if (ws) {
                    var input = document.getElementById("messageText");
                    ws.send(input.value);
                    input.value = '';
                } else {
                    alert("Not connected to WebSocket");
                }
                event.preventDefault();
            }
        </script>
    </body>
</html>

"""

manager = ConnectionManager()


@router.get("/")
async def index():
    return HTMLResponse(index_page)


@router.get("/history/{chat_id}")
async def history(chat_id: int):
    messages = await get_chat_history(chat_id)
    history = []
    for msg in messages:
        m = msg.to_dict()
        m.pop("updated_at")
        history.append(m)

    return {"result": history}


@router.websocket("/chat/{chattype}/{chatname}/{username}")
async def conversation(websocket: WebSocket, chatname: str, username: str, chattype: str = Depends(is_chattype)):

    if chattype == "private":
        chat_hash: str = await hash_of_names(username, chatname)
    elif chattype == "public":
        chat_hash = chatname
        group = await add_member(chatname, username)

    await manager.connect(websocket, chat_hash)

    try:
        while True:
            msg = await websocket.receive_text()

            await manager.send_personal_message(websocket, f"You: {msg}")
            await manager.broadcast(websocket, f"{username.capitalize()}: {msg}", chat_hash)

            read = False
            if chattype == "private":
                if read := await manager.is_active_user(chat_hash):
                    await manager.send_personal_message(websocket, f"<прочитано>")
            elif chattype == "public":
                if read := await manager.is_active_group(chat_hash, group):
                    await manager.send_personal_message(websocket, f"<прочитано>")

            await save_msg(chatname, chattype, username, read, msg)

    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_hash)




