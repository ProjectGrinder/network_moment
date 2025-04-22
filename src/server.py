import asyncio
import websockets
import json

from typing import Dict, List

class User:
    name: str
    pfp: int

    def __init__(self, name, pfp):
        self.name = name
        self.pfp = pfp

class Message:
    user: User
    message: str

    def __init__(self, user, message):
        self.user = user
        self.message = message

class Chat:
    name: str
    admin: List[User]
    public: bool
    whitelist: List[User]
    messages: List[Message]

    def __init__(self, name, admin, public):
        self.name = name
        self.admin = [admin]
        self.public = public
        self.whitelist = []
        self.messages = []
    
    def add_message(self, message: Message):
        self.messages.append(message)


# Global dictionaries for tracking users and chats
connected_users: Dict[websockets.WebSocketServerProtocol, User] = {}
active_chats: Dict[str, Chat] = {}
focused_chats: Dict[str, List[websockets.WebSocketServerProtocol]] = {}  # chatname -> list of clients


# === HELPER FUNCTIONS ===

def broadcast(event_type, data, clients):
    """Send a message to all clients in a specified list."""
    message = json.dumps({"event": event_type, "data": data})
    return asyncio.gather(*(client.send(message) for client in clients))


def user_to_dict(user: User):
    """Convert a User object to a dictionary."""
    return {"username": user.name, "pfp": user.pfp}


def chat_to_dict(chat: Chat):
    """Convert a Chat object to a dictionary."""
    return {
        "chatname": chat.name,
        "public": chat.public,
    }


def chat_detail_to_dict(chat: Chat):
    """Convert detailed Chat information (including messages) to a dictionary."""
    return {
        "chatname": chat.name,
        "admin": [user_to_dict(u) for u in chat.admin],
        "whitelist": [user_to_dict(u) for u in chat.whitelist],
        "messages": [{"user": user_to_dict(m.user), "message": m.message} for m in chat.messages]
    }


# === EVENT HANDLERS ===

async def handle_register_user(ws, data):
    """Handles new user registration."""
    user = User(name=data["username"], pfp=data["pfp"])
    connected_users[ws] = user

    # Broadcast updated user and chat lists to all clients
    await broadcast("update-user-list", [user_to_dict(u) for u in connected_users.values()], connected_users.keys())
    await broadcast("update-chat-list", [chat_to_dict(chat) for chat in active_chats.values()], connected_users.keys())


async def handle_create_chat(ws, data):
    """Handles creating a new chat."""
    user = connected_users[ws]
    chat = Chat(name=data["chatname"], admin=user, public=data["public"])
    
    if not data["public"]:
        chat.whitelist.append(user)

    active_chats[chat.name] = chat
    focused_chats[chat.name] = []

    # Broadcast the new chat to all clients
    await broadcast("update-chat-list", [chat_to_dict(c) for c in active_chats.values()], connected_users.keys())


async def handle_open_chat(ws, data):
    """Handles opening a chat."""
    user = connected_users[ws]
    chat = active_chats.get(data["chatname"])

    if chat and (chat.public or user in chat.whitelist):
        # Focus the chat for this user
        if ws not in focused_chats[chat.name]:
            focused_chats[chat.name].append(ws)

        # Send the chat details to the client
        await ws.send(json.dumps({
            "event": "update-chat-detail",
            "data": chat_detail_to_dict(chat)
        }))
    else:
        # User has no access to the chat
        await ws.send(json.dumps({
            "event": "no-access",
            "data": {
                "message": "Sucks to be you, but you're not whitelisted, bro. Wanna join up?"
            }
        }))


async def handle_post_message(ws, data):
    """Handles posting a message in a chat."""
    user = connected_users[ws]
    chat = active_chats.get(data["chatname"])

    if chat and (chat.public or user in chat.whitelist):
        # Create a new Message object
        message = Message(user=user, message=data["message"])

        # Add the message to the chat
        chat.add_message(message)

        # Broadcast the new message to all clients in the chat
        await broadcast("update-chat-detail", chat_detail_to_dict(chat), focused_chats.get(chat.name, []))


async def handle_join_chat(ws, data):
    """Handles a request for joining a private chat."""
    user = connected_users[ws]
    chat = active_chats.get(data["chatname"])

    if chat and not chat.public:
        # Notify admins of the join request
        await broadcast("join-request", {
            "chatname": chat.name,
            "user": user_to_dict(user)
        }, chat.admin)


async def handle_accept_join_request(ws, data):
    """Handles accepting a join request to add the user to the whitelist."""
    chat = active_chats.get(data["chatname"])
    user = connected_users[ws]

    if chat and user in chat.admin:
        # Find the user to be added
        requested_user = next((u for u in connected_users.values() if u.name == data["username"]), None)

        if requested_user:
            # Add the user to the chat's whitelist
            chat.whitelist.append(requested_user)

            # Notify all users in the chat about the updated details
            await broadcast("update-chat-detail", chat_detail_to_dict(chat), focused_chats.get(chat.name, []))


# === DISPATCHER ===

event_handlers = {
    "register-user": handle_register_user,
    "create-chat": handle_create_chat,
    "open-chat": handle_open_chat,
    "post-message": handle_post_message,
    "join-chat": handle_join_chat,
    "accept-join-request": handle_accept_join_request,
    # Add more handlers here as needed...
}


# === MAIN HANDLER ===

async def handler(ws, path):
    """Main WebSocket handler."""
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
    """Start the WebSocket server."""
    async with websockets.serve(handler, "", port_number):
        await asyncio.Future()  # Run forever
