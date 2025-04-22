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

    async def safe_send(client):
        try:
            await asyncio.wait_for(client.send(message), timeout=5)  # Set a 5-second timeout
        except asyncio.TimeoutError:
            print(f"Timeout: Failed to send message to client {client}")
        except websockets.ConnectionClosed:
            print(f"Connection closed: Failed to send message to client {client}")
        except Exception as e:
            print(f"Error sending message to client {client}: {e}")

    return asyncio.gather(*(safe_send(client) for client in clients))


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
    try:
        username = data.get("username")
        pfp = data.get("pfp")

        # Validate username and profile picture
        if not username or not isinstance(username, str):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "register-user", "message": "Invalid username"}}))
            return
        if not isinstance(pfp, int):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "register-user", "message": "Invalid profile picture ID"}}))
            return

        # Check if the username already exists
        if any(user.name == username for user in connected_users.values()):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "register-user", "message": "Username already taken"}}))
            return

        # Register the user
        user = User(name=username, pfp=pfp)
        connected_users[ws] = user

        # Broadcast updated user and chat lists to all clients
        await broadcast("update-user-list", [user_to_dict(u) for u in connected_users.values()], connected_users.keys())
        await broadcast("update-chat-list", [chat_to_dict(chat) for chat in active_chats.values()], connected_users.keys())
    except Exception as e:
        print(f"Error in handle_register_user: {e}")
        await ws.send(json.dumps({"event": "error", "data": {"event-type": "register-user", "message": "Internal server error"}}))


async def handle_create_chat(ws, data):
    """Handles creating a new chat."""
    try:
        # Validate input data
        chatname = data.get("chatname")
        public = data.get("public")

        if not chatname or not isinstance(chatname, str):
            await ws.send(json.dumps({"event": "error", "data": {"event-type":"create-chat","message": "Invalid or missing chatname"}}))
            return
        if not isinstance(public, bool):
            await ws.send(json.dumps({"event": "error", "data": {"event-type":"create-chat","message": "Invalid or missing public flag"}}))
            return

        # Ensure chatname is unique
        if chatname in active_chats:
            await ws.send(json.dumps({"event": "error", "data": {"event-type":"create-chat","message": "Chatname already exists"}}))
            return

        # Create the chat
        user = connected_users.get(ws)
        if not user:
            await ws.send(json.dumps({"event": "error", "data": {"event-type":"create-chat","message": "User not connected"}}))
            return

        chat = Chat(name=chatname, admin=user, public=public)

        if not public:
            chat.whitelist.append(user)

        active_chats[chat.name] = chat
        focused_chats[chat.name] = []

        # Broadcast the new chat to all clients
        await broadcast("update-chat-list", [chat_to_dict(c) for c in active_chats.values()], connected_users.keys())
    except Exception as e:
        print(f"Error in handle_create_chat: {e}")
        await ws.send(json.dumps({"event": "error", "data": {"event-type":"create-chat","message": "Internal server error"}}))

async def handle_open_chat(ws, data):
    """Handles opening a chat."""
    try:
        # Validate input data
        if not isinstance(data, dict):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "open-chat", "message": "Invalid data format"}}))
            return

        chatname = data.get("chatname")
        if not chatname or not isinstance(chatname, str):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "open-chat", "message": "Invalid or missing chatname"}}))
            return

        # Validate user
        user = connected_users.get(ws)
        if not user:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "open-chat", "message": "User not connected"}}))
            return

        # Validate chat existence
        chat = active_chats.get(chatname)
        if not chat:
            await ws.send(json.dumps({
                "event": "error",
                "data": {
                    "event-type": "open-chat",
                    "message": "Chat doesn't exist."
                }
            }))
            return

        # Check access permissions
        if chat.public or user in chat.whitelist:
            # Remove the user from all current focused chat lists
            for ws_list in focused_chats.values():
                if ws in ws_list:
                    ws_list.remove(ws)

            # Focus the chat for this user
            if ws not in focused_chats[chat.name]:
                focused_chats[chat.name].append(ws)

            # Send chat details to the user
            await ws.send(json.dumps({
                "event": "update-chat-detail",
                "data": chat_detail_to_dict(chat)
            }))
        else:
            # User has no access to the chat
            await ws.send(json.dumps({
                "event": "no-access",
                "data": {
                    "message": "You are not whitelisted for this chat. Request access to join."
                }
            }))
    except Exception as e:
        print(f"Error in handle_open_chat: {e}")
        await ws.send(json.dumps({"event": "error", "data": {"event-type": "open-chat", "message": "Internal server error"}}))


async def handle_post_message(ws, data):
    """Handles posting a message in a chat."""
    user = connected_users[ws]
    chatname = active_chats.get(data["chatname"])
    message_text = data["message"]

    chat = active_chats.get(chatname)
    if not chat:
        return

    # Check access
    if not (chat.public or user in chat.whitelist):
        await ws.send(json.dumps({
            "event": "no-access",
            "data": {
                "message": "Sucks to be you, but you're not whitelisted, bro. Wanna join up?"
            }
        }))
        return

    # Add message
    new_msg = Message(user, message_text)
    chat.add_message(new_msg)

    # Send update to focused clients only
    clients = focused_chats.get(chatname, [])
    await broadcast("update-chat-detail", chat_detail_to_dict(chat), clients)


async def handle_join_chat(ws, data):
    """Handles a request for joining a private chat."""
    try:
        # Validate input data
        if not isinstance(data, dict):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "join-chat", "message": "Invalid data format"}}))
            return

        chatname = data.get("chatname")
        if not chatname or not isinstance(chatname, str):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "join-chat", "message": "Invalid or missing chatname"}}))
            return

        # Validate user
        user = connected_users.get(ws)
        if not user:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "join-chat", "message": "User not connected"}}))
            return

        # Validate chat existence
        chat = active_chats.get(chatname)
        if not chat:
            await ws.send(json.dumps({
                "event": "error",
                "data": {
                    "event-type": "join-chat",
                    "message": "Chat doesn't exist."
                }
            }))
            return

        # Check if the chat is public
        if chat.public:
            await ws.send(json.dumps({
                "event": "error",
                "data": {
                    "event-type": "join-chat",
                    "message": "This is a public chat. No join request is needed."
                }
            }))
            return

        # Notify chat admins about the join request
        for client_ws, admin_user in connected_users.items():
            if admin_user in chat.admin:
                await client_ws.send(json.dumps({
                    "event": "join-request",
                    "data": {
                        "chatname": chat.name,
                        "user": user_to_dict(user)
                    }
                }))
    except Exception as e:
        print(f"Error in handle_join_chat: {e}")
        await ws.send(json.dumps({"event": "error", "data": {"event-type": "join-chat", "message": "Internal server error"}}))


async def handle_accept_join_request(ws, data):
    """Handles accepting a join request to add the user to the whitelist."""
    try:
        # Validate input data
        if not isinstance(data, dict):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "accept-join-request", "message": "Invalid data format"}}))
            return

        chatname = data.get("chatname")
        username = data.get("username")
        if not chatname or not isinstance(chatname, str):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "accept-join-request", "message": "Invalid or missing chatname"}}))
            return
        if not username or not isinstance(username, str):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "accept-join-request", "message": "Invalid or missing username"}}))
            return

        # Validate admin user
        admin = connected_users.get(ws)
        if not admin:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "accept-join-request", "message": "User not connected"}}))
            return

        # Validate chat existence and admin privileges
        chat = active_chats.get(chatname)
        if not chat:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "accept-join-request", "message": "Chat does not exist"}}))
            return
        if admin not in chat.admin:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "accept-join-request", "message": "You are not an admin of this chat"}}))
            return

        # Find the user to add by username
        user_to_add = None
        for client_ws, user in connected_users.items():
            if user.name == username:
                user_to_add = user
                break

        if not user_to_add:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "accept-join-request", "message": "User not found"}}))
            return

        # Add the user to the whitelist if not already present
        if user_to_add not in chat.whitelist:
            chat.whitelist.append(user_to_add)

        # Update all focused clients
        focused = focused_chats.get(chat.name, [])
        await broadcast("update-chat-detail", chat_detail_to_dict(chat), focused)

        # Notify the admins and the newly whitelisted user that the request is resolved
        for client_ws, user in connected_users.items():
            if user == user_to_add or user in chat.admin:
                await client_ws.send(json.dumps({
                    "event": "resolve-join-request",
                    "data": {
                        "chatname": chatname,
                        "user": user_to_dict(user_to_add),
                        "accept": True
                    }
                }))
    except Exception as e:
        print(f"Error in handle_accept_join_request: {e}")
        await ws.send(json.dumps({"event": "error", "data": {"event-type": "accept-join-request", "message": "Internal server error"}}))


async def handle_reject_join_request(ws, data):
    """Handles rejecting a join request for a private chat."""
    try:
        # Validate input data
        if not isinstance(data, dict):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "reject-join-request", "message": "Invalid data format"}}))
            return

        chatname = data.get("chatname")
        username = data.get("username")
        if not chatname or not isinstance(chatname, str):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "reject-join-request", "message": "Invalid or missing chatname"}}))
            return
        if not username or not isinstance(username, str):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "reject-join-request", "message": "Invalid or missing username"}}))
            return

        # Validate admin user
        admin = connected_users.get(ws)
        if not admin:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "reject-join-request", "message": "User not connected"}}))
            return

        # Validate chat existence and admin privileges
        chat = active_chats.get(chatname)
        if not chat:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "reject-join-request", "message": "Chat does not exist"}}))
            return
        if admin not in chat.admin:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "reject-join-request", "message": "You are not an admin of this chat"}}))
            return

        # Find the user to reject by username
        user_to_reject = None
        for client_ws, user in connected_users.items():
            if user.name == username:
                user_to_reject = user
                break

        if not user_to_reject:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "reject-join-request", "message": "User not found"}}))
            return

        # Notify the admins and the rejected user that the request is resolved
        for client_ws, user in connected_users.items():
            if user == user_to_reject or user in chat.admin:
                await client_ws.send(json.dumps({
                    "event": "resolve-join-request",
                    "data": {
                        "chatname": chatname,
                        "user": user_to_dict(user_to_reject),
                        "accept": False
                    }
                }))
    except Exception as e:
        print(f"Error in handle_reject_join_request: {e}")
        await ws.send(json.dumps({"event": "error", "data": {"event-type": "reject-join-request", "message": "Internal server error"}}))

async def handle_remove_user(ws, data):
    admin = connected_users[ws]
    chatname = data["chatname"]
    target_username = data["username"]

    chat = active_chats.get(chatname)
    if not chat or admin not in chat.admin:
        return

    # Find the target user and their websocket
    for client_ws, user in connected_users.items():
        if user.name == target_username:
            if user in chat.whitelist:
                chat.whitelist.remove(user)

            if user in chat.admin:
                chat.admin.remove(user)

            # if they were focused on this chat, remove their focus.
            if client_ws in focused_chats.get(chatname, []):
                focused_chats[chatname].remove(client_ws)

            # Notify the kicked user
            await client_ws.send(json.dumps({
                "event": "revoke-access",
                "data": {
                    "chatname": chatname
                }
            }))
            break  # Stop once we've found and handled the user

    # Notify all focused clients with updated chat detail
    focused = focused_chats.get(chatname, [])
    await broadcast("update-chat-detail", chat_detail_to_dict(chat), focused)

async def handle_inbox(ws, data):
    """Sends a message to the target client's inbox."""
    sender = connected_users.get(ws)
    target_username = data["username"]
    message = data["message"]

    for client_ws, user in connected_users.items():
        if user.name == target_username:
            await client_ws.send(json.dumps({
                "event": "update-inbox",
                "data": {
                    "sender": user_to_dict(sender),
                    "message": message
                }
            }))
            break

async def handle_add_admin(ws, data):
    """Adds a user as an admin to the chatroom."""
    admin = connected_users.get(ws)
    chatname = data["chatname"]
    target_username = data["username"]
    chat = active_chats.get(chatname)
    if not chat or admin not in chat.admin:
        return
    
    user_to_add = None
    for client_ws, user in connected_users.items():
        if user.name == target_username:
            user_to_add = user

    if not user_to_add:
        return
    
    if user_to_add not in chat.admin:
        chat.admin.append(user_to_add)
        await client_ws.send(json.dumps({
            "event": "update-chat-detail",
            "data": chat_detail_to_dict(chat)
        }))


# === DISPATCHER ===

event_handlers = {
    "register-user": handle_register_user,
    "create-chat": handle_create_chat,
    "open-chat": handle_open_chat,
    "post-message": handle_post_message,
    "join-chat": handle_join_chat,
    "accept-join-request": handle_accept_join_request,
    "reject-join-request": handle_reject_join_request,
    "remove-user": handle_remove_user,
    "inbox": handle_inbox,
    "add-admin": handle_add_admin
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
