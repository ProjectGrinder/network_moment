from pprint import pprint
import asyncio
import json
from urllib.parse import quote, unquote

from src.requests.request import Request
from src.requests.type import REQUEST_TYPE
from src.response import make_response
from src.requests.header import Header

class User:
    name: str
    pfp: int

    def __init__(self, name, pfp):
        self.name = name
        self.pfp = pfp

class Chat:
    name: str
    admin: list[User]
    public: bool
    whitelist: list[User]

    def __init__(self, name, admin, public):
        self.name = name
        self.admin = admin
        self.public = public
        self.whitelist = []

class Api:
    users: list[User]
    groups: list[Chat]
    sse_clients: set

    def __init__(self):
        self.users = []
        self.groups = []
        self.sse_clients = set()

    async def handle(self, loop: asyncio.AbstractEventLoop, client, addr, request: Request):
        pprint(request)
        
        method = request.type
        path = request.path

        response = None

        if method == REQUEST_TYPE.GET and path == "/api/status": #OK
            response = await self.status(request)

        if method == REQUEST_TYPE.GET and path == "/api/chat": #OK
            response = await self.get_all_chats(request)

        elif method == REQUEST_TYPE.POST and path == "/api/chat/create": #OK
            response = await self.create_chat(request)

        elif method == REQUEST_TYPE.GET and path == "/api/users": #OK
            response = await self.get_users(request)

        elif method == REQUEST_TYPE.POST and path == "/api/users": #OK
            response = await self.register_user(request)

        elif method == REQUEST_TYPE.GET and path == "/api/events": #OK
            await self.handle_sse(loop, client, request)
            return

        elif method == REQUEST_TYPE.POST and path.startswith("/api/chat/") and path.count("/") == 3:
            chatname = path.split("/")[-1]
            response = await self.post_chat_message(request, chatname)

        elif method == REQUEST_TYPE.POST and path.startswith("/api/chat/") and path.endswith("/join") and path.count("/") == 4:
            chatname = path.split("/")[3]
            response = await self.join_chat(request, chatname)

        elif method == REQUEST_TYPE.PUT and path.startswith("/api/chat/") and path.endswith("/approve") and path.count("/") == 4:
            chatname = path.split("/")[3]
            response = await self.approve_join(request, chatname)

        elif method == REQUEST_TYPE.DELETE and path.startswith("/api/chat/") and path.endswith("/reject") and path.count("/") == 4:
            chatname = path.split("/")[3]
            response = await self.reject_join(request, chatname)

        elif method == REQUEST_TYPE.DELETE and path.startswith("/api/chat/") and path.count("/") == 3:
            chatname = path.split("/")[-1]
            response = await self.remove_user(request, chatname)

        else:
            response = make_response("Not Found", 404)

        if response:
            await loop.sock_sendall(client, response.encode())

        client.close()

    # Routes

    # GET /api/status
    async def status(self, request: Request) -> str:
        return make_response("OK", 200)

    # GET /api/chat
    async def get_all_chats(self, request: Request) -> str:
        return make_response(json.dumps([group.__dict__ for group in self.groups]), 200)

    # POST /api/chat/:chatname
    async def post_chat_message(self, request: Request, chatname: str) -> str:
        try:
            message_data = json.loads(request.body)
            chatname = unquote(chatname)

            if "message" not in message_data:
                return make_response("Bad Request", 400)
            
            if "user" not in message_data:
                return make_response("Bad Request", 400)
            
            message = message_data["message"]
            user = message_data["user"]
            
            this_chat = None
            for group in self.groups:
                if group.name == chatname:
                    this_chat = group
                    break
            if this_chat == None:
                return make_response("Not Found", 404)
            
            if (not this_chat.public) and (user not in this_chat.whitelist):
                return make_response("Forbidden", 403)

            await self.broadcast_event("chat-message", json.dumps({"chatname": quote(chatname), "user": user, "message": message}))

            return make_response("OK", 200)
        
        except (json.JSONDecodeError, KeyError) as e:
            return make_response("Bad Request", 400)

    # POST /api/chat/create
    async def create_chat(self, request: Request) -> str:
            message_data = json.loads(request.body)

            name = message_data["name"]
            user = message_data["user"]
            public = message_data["public"]

            if user not in [user.name for user in self.users]:
                return make_response("Not Found", 404)

            this_chat = Chat(name, user, public)
            if not this_chat.public:
                this_chat.whitelist.append(user)

            self.groups.append(this_chat)

            chat_message = this_chat.__dict__
            chat_message["name"] = quote(this_chat.name)
            await self.broadcast_event("chat-message", json.dumps(chat_message))

            return make_response("Created", 201)

    # GET /api/chat/:chatname/join
    async def join_chat(self, request: Request, chatname: str) -> str:
        try:
            chatname = unquote(chatname)
            message_data = json.loads(request.body)
            user = message_data["user"]

            this_chat = None
            for chat in self.groups:
                if chat.name == chatname:
                    this_chat = chat
                    break
            if this_chat == None:
                return make_response("Not Found", 404)
            
            if this_chat.public:
                return make_response(json.dumps({"message": "Public room. You can join directly."}), 200, "application/json")
            
            await self.broadcast_event("join-request", json.dumps({"chatname": quote(chatname), "user": user}))

            return make_response("OK", 200)

        except (json.JSONDecodeError, KeyError) as e:
            return make_response("Bad Request", 400)

    # PUT /api/chat/:chatname/approve
    async def approve_join(self, request: Request, chatname: str) -> str:
        try:
            chatname = unquote(chatname)
            message_data = json.loads(request.body)
            user = message_data["user"]

            this_chat = None
            for chat in self.groups:
                if chat.name == chatname:
                    this_chat = chat
                    break
            if this_chat == None:
                return make_response("Not Found", 404)
            
            if(user not in [user.name for user in self.users]):
                return make_response("Not Found", 404)
            
            # MISSING: admin authorization (403 Forbidden)
            this_chat.whitelist.append(user)
            await self.broadcast_event("approve-join-request", json.dumps({"chatname": quote(chatname), "user": user}))

            return make_response("OK", 200)

        except (json.JSONDecodeError, KeyError) as e:
            return make_response("Bad Request", 400)
    
    # PUT /api/chat/:chatname/reject
    async def reject_join(self, request: Request, chatname: str) -> str:
        try:
            chatname = unquote(chatname)
            message_data = json.loads(request.body)
            user = message_data["user"]

            this_chat = None
            for chat in self.groups:
                if chat.name == chatname:
                    this_chat = chat
                    break
            if this_chat == None:
                return make_response("Not Found", 404)
            
            if(user not in [user.name for user in self.users]):
                return make_response("Not Found", 404)
            
            # MISSING: admin authorization (403 Forbidden)
            
            await self.broadcast_event("reject-join-request", json.dumps({"chatname": quote(chatname), "user": user}))

            return make_response("OK", 200)

        except (json.JSONDecodeError, KeyError) as e:
            return make_response("Bad Request", 400)

    # DELETE /api/chat/:chatname
    async def remove_user(self, request: Request, chatname: str) -> str:
        try:
            chatname = unquote(chatname)
            message_data = json.loads(request.body)
            user = message_data["user"]

            this_chat = None
            for chat in self.groups:
                if chat.name == chatname:
                    this_chat = chat
                    break
            if this_chat == None:
                return make_response("Not Found", 404)
            
            if(user not in [user.name for user in self.users]):
                return make_response("Not Found", 404)

            if(user not in this_chat.whitelist):
                return make_response("Not Found", 404)
            
            # MISSING: admin authorization (403 Forbidden)

            this_chat.whitelist.remove(user)
            
            await self.broadcast_event("remove-user", json.dumps({"chatname": quote(chatname), "user": user}))

            return make_response("OK", 200)

        except (json.JSONDecodeError, KeyError) as e:
            return make_response("Bad Request", 400)

    # GET /api/users
    async def get_users(self, request: Request) -> str:
        return make_response(json.dumps([user.__dict__ for user in self.users]), 200)

    # POST /api/users
    async def register_user(self, request: Request) -> str:
        try:
            message_data = json.loads(request.body)
            user = message_data["user"]
            pfp = message_data["pfp"]

            
            if(user in [user.name for user in self.users]):
                return make_response("Conflict", 409)

            self.users.append(User(user, pfp))
            
            await self.broadcast_event("register-user", json.dumps({"name": user, "pfp": pfp}))

            return make_response("OK", 200)

        except (json.JSONDecodeError, KeyError) as e:
            return make_response("Bad Request", 400)

    # GET /api/events (SSE)
    async def handle_sse(self, loop, client, request: Request) -> None:

        headers = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/event-stream\r\n"
            "Cache-Control: no-cache\r\n"
            "Connection: keep-alive\r\n"
            "\r\n"
        )

        # Send keep-alive header
        await loop.sock_sendall(client, headers.encode())

        self.sse_clients.add(client)
        try:
            while True:
                # Example: send a heartbeat event every 10 seconds
                await asyncio.sleep(10)
                msg = "event: heartbeat\ndata: ping\n\n"
                await loop.sock_sendall(client, msg.encode())
        except (ConnectionResetError, BrokenPipeError):
            # Client disconnected
            pass
        finally:
            self.sse_clients.discard(client)
            client.close()
    
    # SSE methods

    async def broadcast_event(self, event: str, data: str):
        loop = asyncio.get_running_loop()
        msg = f"event: {event}\ndata: {data}\n\n"
        for client in list(self.sse_clients):
            try:
                await loop.sock_sendall(client, msg.encode())
            except (ConnectionResetError, BrokenPipeError):
                self.sse_clients.discard(client)
                client.close()