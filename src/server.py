import asyncio
import websockets
import json

from typing import Dict, List

class User:
    name: str
    pfp: int

    def __init__(self, name, pfp, token):
        self.name = name
        self.pfp = pfp

class Chat:
    name: str
    admin: list[User]
    public: bool
    whitelist: list[User]

    def __init__(self, name, admin, public):
        self.name = name
        self.admin = [admin]
        self.public = public
        self.whitelist = []

# Assume User and Chat classes are already defined
connected_users: Dict[websockets.WebSocketServerProtocol, User] = {}
active_chats: Dict[str, Chat] = {}
focused_chats: Dict[str, List[websockets.WebSocketServerProtocol]] = {}  # chatname -> list of clients


# === HELPER FUNCTIONS ===

def broadcast(event_type, data, clients):
    message = json.dumps({"event": event_type, "data": data})
    return asyncio.gather(*(client.send(message) for client in clients))


def user_to_dict(user: User):
    return {"username": user.name, "pfp": user.pfp}


def chat_to_dict(chat: Chat):
    return {
        "chatname": chat.name,
        "public": chat.public,
    }


def chat_detail_to_dict(chat: Chat, messages=[]):
    return {
        "chatname": chat.name,
        "admin": [user_to_dict(u) for u in chat.admin],
        "whitelist": [user_to_dict(u) for u in chat.whitelist],
        "messages": [{"user": user_to_dict(m["user"]), "message": m["message"]} for m in messages]
    }


# === EVENT HANDLERS ===

async def handle_register_user(ws, data):
    user = User(name=data["username"], pfp=data["pfp"], token=None)
    connected_users[ws] = user

    await broadcast("update-user-list", [user_to_dict(u) for u in connected_users.values()], connected_users.keys())
    await broadcast("update-chat-list", [chat_to_dict(chat) for chat in active_chats.values()], connected_users.keys())


async def handle_create_chat(ws, data):
    user = connected_users[ws]
    chat = Chat(name=data["chatname"], admin=user, public=data["public"])
    if not data["public"]:
        chat.whitelist.append(user)

    active_chats[chat.name] = chat
    focused_chats[chat.name] = []

    await broadcast("update-chat-list", [chat_to_dict(c) for c in active_chats.values()], connected_users.keys())


async def handle_open_chat(ws, data):
    user = connected_users[ws]
    chat = active_chats.get(data["chatname"])

    if chat.public or user in chat.whitelist:
        if ws not in focused_chats[chat.name]:
            focused_chats[chat.name].append(ws)

        await ws.send(json.dumps({
            "event": "update-chat-detail",
            "data": chat_detail_to_dict(chat)
        }))
    else:
        await ws.send(json.dumps({
            "event": "no-access",
            "data": {
                "message": "Sucks to be you, but you're not whitelisted, bro. Wanna join up?"
            }
        }))


# More handlers like handle_post_message, handle_join_chat, etc. can be added here.


# === DISPATCHER ===

event_handlers = {
    "register-user": handle_register_user,
    "create-chat": handle_create_chat,
    "open-chat": handle_open_chat,
    # Add more handlers here...
}


# === MAIN HANDLER ===

async def handler(ws, path):
    try:
        async for message in ws:
            try:
                payload = json.loads(message)
                event = payload.get("event")
                data = payload.get("data")

                if event in event_handlers:
                    await event_handlers[event](ws, data)
                else:
                    print(f"Unknown event: {event}")

            except Exception as e:
                print(f"Error handling message: {e}")

    finally:
        # Cleanup on disconnect
        if ws in connected_users:
            del connected_users[ws]
        for chat_ws_list in focused_chats.values():
            if ws in chat_ws_list:
                chat_ws_list.remove(ws)
        await broadcast("update-user-list", [user_to_dict(u) for u in connected_users.values()], connected_users.keys())


# === SERVER STARTUP ===

async def main(port_number: int):
    async with websockets.serve(handler, "", port_number):
        await asyncio.Future()  # Run forever
