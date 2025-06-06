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
    pfp: int
    admin: List[User]
    public: bool
    whitelist: List[User]
    messages: List[Message]

    def __init__(self, name, pfp, admin, public):
        self.name = name
        self.pfp = pfp
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
            print(f"Connection closed: Removing client {client}")
            if client in connected_users:
                del connected_users[client]
            for chat_ws_list in focused_chats.values():
                if client in chat_ws_list:
                    chat_ws_list.remove(client)
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
        "pfp": chat.pfp,
        "public": chat.public,
    }


def chat_detail_to_dict(chat: Chat):
    """Convert detailed Chat information (including messages) to a dictionary."""
    return {
        "chatname": chat.name,
        "pfp": chat.pfp,
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
        pfp = data.get("pfp")
        public = data.get("public")

        if not chatname or not isinstance(chatname, str):
            await ws.send(json.dumps({"event": "error", "data": {"event-type":"create-chat","message": "Invalid or missing chatname"}}))
            return
        if not isinstance(pfp, int):
            await ws.send(json.dumps({"event": "error", "data": {"event-type":"create-chat", "message": "Invalid or missing profile picture ID"}}))
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

        chat = Chat(name=chatname, pfp=pfp, admin=user, public=public)
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
            # If the chat is public, add the user to the whitelist
            if chat.public and user not in chat.whitelist:
                chat.whitelist.append(user)

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
    chatname = data.get("chatname")
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
    """Handles removing a user from a chat, including other admins."""
    try:
        # Validate input data
        if not isinstance(data, dict):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "remove-user", "message": "Invalid data format"}}))
            return

        chatname = data.get("chatname")
        target_username = data.get("username")
        if not chatname or not isinstance(chatname, str):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "remove-user", "message": "Invalid or missing chatname"}}))
            return
        if not target_username or not isinstance(target_username, str):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "remove-user", "message": "Invalid or missing username"}}))
            return

        # Validate admin user
        admin = connected_users.get(ws)
        if not admin:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "remove-user", "message": "User not connected"}}))
            return

        # Validate chat existence and admin privileges
        chat = active_chats.get(chatname)
        if not chat:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "remove-user", "message": "Chat does not exist"}}))
            return
        if admin not in chat.admin:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "remove-user", "message": "You are not an admin of this chat"}}))
            return

        # Find the target user and their websocket
        target_user_ws = None
        target_user = None
        for client_ws, user in connected_users.items():
            if user.name == target_username:
                target_user_ws = client_ws
                target_user = user
                break

        if not target_user:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "remove-user", "message": "User not found"}}))
            return

        # Remove the user from the chat's whitelist and admin list
        if target_user in chat.whitelist:
            chat.whitelist.remove(target_user)
        if target_user in chat.admin:
            chat.admin.remove(target_user)

        # Remove the user's focus on the chat if applicable
        if target_user_ws in focused_chats.get(chatname, []):
            focused_chats[chatname].remove(target_user_ws)

        # Notify the removed user
        await target_user_ws.send(json.dumps({
            "event": "revoke-access",
            "data": {
                "chatname": chatname
            }
        }))

        # Check if no admins remain
        if len(chat.admin) == 0:
            del active_chats[chatname]
            if chatname in focused_chats:
                del focused_chats[chatname]
            
            # Notify all clients about the deleted chat
            await broadcast("delete-chat", {"chatname": chatname}, connected_users.keys())
        else:
            # Notify all focused clients with updated chat details
            focused = focused_chats.get(chatname, [])
            await broadcast("update-chat-detail", chat_detail_to_dict(chat), focused)

    except Exception as e:
        print(f"Error in handle_remove_user: {e}")
        await ws.send(json.dumps({"event": "error", "data": {"event-type": "remove-user", "message": "Internal server error"}}))

async def handle_inbox(ws, data):
    """Sends a message to the target client's inbox."""
    try:
        # Validate input data
        if not isinstance(data, dict):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "inbox", "message": "Invalid data format"}}))
            return

        target_username = data.get("username")
        message = data.get("message")
        if not target_username or not isinstance(target_username, str):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "inbox", "message": "Invalid or missing target username"}}))
            return
        if not message or not isinstance(message, str):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "inbox", "message": "Invalid or missing message"}}))
            return

        # Validate sender
        sender = connected_users.get(ws)
        if not sender:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "inbox", "message": "Sender not connected"}}))
            return

        # Find the target user
        target_user_ws = None
        for client_ws, user in connected_users.items():
            if user.name == target_username:
                target_user_ws = client_ws
                break

        if not target_user_ws:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "inbox", "message": "Target user not found"}}))
            return

        # Send the message to the target user's inbox
        await target_user_ws.send(json.dumps({
            "event": "update-inbox",
            "data": {
                "sender": user_to_dict(sender),
                "message": message
            }
        }))
    except Exception as e:
        print(f"Error in handle_inbox: {e}")
        await ws.send(json.dumps({"event": "error", "data": {"event-type": "inbox", "message": "Internal server error"}}))

async def handle_add_admin(ws, data):
    """Adds a user as an admin to the chatroom."""
    try:
        # Validate input data
        if not isinstance(data, dict):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "add-admin", "message": "Invalid data format"}}))
            return

        chatname = data.get("chatname")
        target_username = data.get("username")
        if not chatname or not isinstance(chatname, str):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "add-admin", "message": "Invalid or missing chatname"}}))
            return
        if not target_username or not isinstance(target_username, str):
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "add-admin", "message": "Invalid or missing username"}}))
            return

        # Validate admin user
        admin = connected_users.get(ws)
        if not admin:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "add-admin", "message": "User not connected"}}))
            return

        # Validate chat existence and admin privileges
        chat = active_chats.get(chatname)
        if not chat:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "add-admin", "message": "Chat does not exist"}}))
            return
        if admin not in chat.admin:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "add-admin", "message": "You are not an admin of this chat"}}))
            return

        # Find the user to add as admin
        user_to_add = None
        for client_ws, user in connected_users.items():
            if user.name == target_username:
                user_to_add = user
                break

        if not user_to_add:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "add-admin", "message": "User not found"}}))
            return

        # Ensure the user is whitelisted in the chat
        if user_to_add not in chat.whitelist:
            await ws.send(json.dumps({"event": "error", "data": {"event-type": "add-admin", "message": "User is not whitelisted in this chat"}}))
            return

        # Add the user as an admin if not already an admin
        if user_to_add not in chat.admin:
            chat.admin.append(user_to_add)

            # Notify all focused clients with updated chat details
            focused = focused_chats.get(chatname, [])
            await broadcast("update-chat-detail", chat_detail_to_dict(chat), focused)

            # Notify the newly added admin
            for client_ws, user in connected_users.items():
                if user == user_to_add:
                    await client_ws.send(json.dumps({
                        "event": "update-chat-detail",
                        "data": chat_detail_to_dict(chat)
                    }))
                    break
    except Exception as e:
        print(f"Error in handle_add_admin: {e}")
        await ws.send(json.dumps({"event": "error", "data": {"event-type": "add-admin", "message": "Internal server error"}}))

async def handle_get_user(ws, data):
    try:
        await ws.send(json.dumps({"event": "update-user-list", "data": [user_to_dict(u) for u in connected_users.values()]}))
    except Exception as e:
        print(f"Error in handle_get_user: {e}")
        await ws.send(json.dumps({"event": "error", "data": {"event-type": "get-user", "message": "Internal server error"}}))

async def handle_get_chat(ws, data):
    try:
        await ws.send(json.dumps({"event": "update-chat-list", "data": [chat_to_dict(c) for c in active_chats.values()]}))
    except Exception as e:
        print(f"Error in handle_get_chat: {e}")
        await ws.send(json.dumps({"event": "error", "data": {"event-type": "get-chat", "message": "Internal server error"}}))

async def handle_get_data(ws, data):
    try:
        await ws.send(json.dumps({"event": "update-user-list", "data": [user_to_dict(u) for u in connected_users.values()]}))
        await ws.send(json.dumps({"event": "update-chat-list", "data": [chat_to_dict(c) for c in active_chats.values()]}))
        for chatname, ws_list in focused_chats.items():
            if ws in ws_list:
                chat = active_chats.get(chatname)
            if chat:
                await ws.send(json.dumps({
                    "event": "update-chat-detail",
                    "data": chat_detail_to_dict(chat)
                }))
            return
        # If no focused chat is found, notify the user
        await ws.send(json.dumps({
            "event": "error",
            "data": {
                "event-type": "get-data",
                "message": "No focused chat found for this user"
            }
        }))
    except Exception as e:
        print(f"Error in handle_get_chat: {e}")
        await ws.send(json.dumps({"event": "error", "data": {"event-type": "get-chat", "message": "Internal server error"}}))

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
    "add-admin": handle_add_admin,
    "get-user": handle_get_user,
    "get-chat": handle_get_chat,
    "get-data": handle_get_data
    # Add more handlers here as needed...
}


# === MAIN HANDLER ===

async def handler(ws):
    """Main WebSocket handler with heartbeat mechanism."""
    disconnect_event = asyncio.Event()

    # Start a background task to send pings
    async def send_heartbeat():
        try:
            while not disconnect_event.is_set():
                try:
                    await ws.send(json.dumps({"event": "heartbeat", "data": {"ping": "!"}}))
                    await asyncio.sleep(30)  # Send a ping every 30 seconds
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"Heartbeat error: {e}")
                    disconnect_event.set()
                    break
        finally:
            disconnect_event.set()

    heartbeat_task = asyncio.create_task(send_heartbeat())

    try:
        async for message in ws:
            try:
                # Parse and validate the payload
                payload = json.loads(message)
                if not isinstance(payload, dict):
                    await ws.send(json.dumps({"event": "error", "data": {"message": "Invalid payload format"}}))
                    continue

                event = payload.get("event")
                data = payload.get("data")
                if not event or not isinstance(event, str):
                    await ws.send(json.dumps({"event": "error", "data": {"message": "Invalid or missing event type"}}))
                    continue

                if event in event_handlers:
                    await event_handlers[event](ws, data)
                else:
                    await ws.send(json.dumps({"event": "error", "data": {"message": f"Unknown event: {event}"}}))

            except json.JSONDecodeError:
                await ws.send(json.dumps({"event": "error", "data": {"message": "Invalid JSON format"}}))
            except websockets.ConnectionClosed:
                print(f"Connection closed for client {ws}")
            except Exception as e:
                print(f"Error handling message: {e}")
                await ws.send(json.dumps({"event": "error", "data": {"message": "Internal server error"}}))

    except Exception as e:
        print(f"Unexpected error in handler: {e}")
    finally:
        # Cancel the heartbeat task
        disconnect_event.set()
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass

        # Cleanup on disconnect
        user = connected_users.pop(ws, None)
        if user:
            # Remove the user from all active chats
            chats_to_delete = []
            for chatname, chat in active_chats.items():
                if user in chat.whitelist:
                    chat.whitelist.remove(user)
                if user in chat.admin:
                    chat.admin.remove(user)
                # If no admins remain, mark the chat for deletion
                if len(chat.admin) == 0:
                    chats_to_delete.append(chatname)
                else:
                    # Broadcast updated chat details if the chat isn't marked for deletion
                    focused = focused_chats.get(chatname, [])
                    await broadcast("update-chat-detail", chat_detail_to_dict(chat), focused)

            # Delete chats with no admins and notify clients
            for chatname in chats_to_delete:
                del active_chats[chatname]
                if chatname in focused_chats:
                    del focused_chats[chatname]
                await broadcast("delete-chat", {"chatname": chatname}, connected_users.keys())

        # Remove the WebSocket from focused chats
        for chat_ws_list in focused_chats.values():
            if ws in chat_ws_list:
                chat_ws_list.remove(ws)

        # Broadcast updated user list
        await broadcast("update-user-list", [user_to_dict(u) for u in connected_users.values()], connected_users.keys())
# === SERVER STARTUP ===

async def main(port_number: int):
    """Start the WebSocket server."""
    try:
        async with websockets.serve(handler, "", port_number):
            print(f"WebSocket server started on port {port_number}")
            await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        print("\nWebSocket server stopped by user")