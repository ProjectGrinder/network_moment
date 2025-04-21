from pprint import pprint
import asyncio
import json
from urllib.parse import quote, unquote

from src.requests.request import Request
from src.requests.type import REQUEST_TYPE
from src.response import make_response
from src.requests.header import Header
import secrets

class User:
    name: str
    pfp: int
    token: str

    def __init__(self, name, pfp, token):
        self.name = name
        self.pfp = pfp
        self.token = token

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

        elif method == REQUEST_TYPE.GET and path.startswith("/api/events"):
            token = path.split("/")[-1]
            await self.handle_sse(loop, client, request, token)
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
            response = await self.frontend_serve(request)

        if response:
            await loop.sock_sendall(client, response.encode())

        client.close()

    # Frontend Routes (Dynamic)
    async def frontend_serve(self, request: Request):
        path = "/dist" + request.path
        try:
            with open(path, "rb") as f:
                body = f.read()
            return make_response(body, 200, "text/html")
        except FileNotFoundError:
            return make_response("Not Found", 404)

    # API Routes

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
            
            if "token" not in message_data:
                return make_response("Bad Request", 400)
            
            message = message_data["message"]
            token = message_data["token"]

            this_user = None
            for user in self.users:
                if user.token == token:
                    this_user = user
                    break
            if this_user == None:
                return make_response("Forbidden", 403)

            this_chat = None
            for group in self.groups:
                if group.name == chatname:
                    this_chat = group
                    break
            if this_chat == None:
                return make_response("Not Found", 404)
            
            if (not this_chat.public) and (user not in this_chat.whitelist):
                return make_response("Forbidden", 403)

            await self.broadcast_event("chat-message", 
                                       json.dumps({
                                           "chatname": quote(chatname), 
                                           "user": {
                                               "name": this_user.name, 
                                               "pfp": this_user.pfp
                                               }, 
                                            "message": message}))

            return make_response("OK", 200)
        
        except (json.JSONDecodeError, KeyError) as e:
            return make_response("Bad Request", 400)

    # POST /api/chat/create
    async def create_chat(self, request: Request) -> str:
            message_data = json.loads(request.body)

            name = message_data["name"]
            token = message_data["token"]
            public = message_data["public"]

            this_user = None
            for user in self.users:
                if user.token == token:
                    this_user = user
            if(this_user == None):
                return make_response("Forbidden", 403)

            this_chat = Chat(name, user, public)
            if not this_chat.public:
                this_chat.whitelist.append(this_user)

            self.groups.append(this_chat)

            message = this_chat.__dict__
            message["name"] = quote(this_chat.name)
            message["admin"] = {"name": this_user.name, "pfp": this_user.pfp}
            await self.broadcast_event("create_chat", json.dumps({
                "name": this_chat.name,
                "admin": {
                    "name": this_user.name,
                    "pfp": this_user.pfp
                },
                "public": this_chat.public,
                "whitelist": [{"name": user.name, "pfp": user.pfp} for user in this_chat.whitelist]
            }))

            return make_response("Created", 201)

    # GET /api/chat/:chatname/join
    async def join_chat(self, request: Request, chatname: str) -> str:
        try:
            chatname = unquote(chatname)
            message_data = json.loads(request.body)
            token = message_data["token"]

            this_user = None
            for user in self.users:
                if user.token == token:
                    this_user = user
                    break
            if this_user == None:
                return make_response("Forbidden", 403)

            this_chat = None
            for chat in self.groups:
                if chat.name == chatname:
                    this_chat = chat
                    break
            if this_chat == None:
                return make_response("Not Found", 404)
            
            if this_chat.public:
                return make_response(json.dumps({"message": "Public room. You can join directly."}), 200, "application/json")
            
            await self.broadcast_event("join-request", json.dumps({"chatname": quote(chatname), "user": {"name": this_user.name, "pfp": this_user.pfp}}))

            return make_response("OK", 200)

        except (json.JSONDecodeError, KeyError) as e:
            return make_response("Bad Request", 400)

    # PUT /api/chat/:chatname/approve
    async def approve_join(self, request: Request, chatname: str) -> str:
        try:
            chatname = unquote(chatname)
            message_data = json.loads(request.body)
            target = message_data["user"]
            token = message_data["token"]

            this_chat = None
            for chat in self.groups:
                if chat.name == chatname:
                    this_chat = chat
                    break
            if this_chat == None:
                return make_response("Not Found", 404)
            
            this_user = None
            for user in self.users:
                if user.name == target:
                    this_user = user
            if this_user == None:
                return make_response("Not Found", 404)
            
            this_admin = None
            for admin in this_chat.admin:
                if admin.token == token:
                    this_admin = token
            if this_admin == None:
                return make_response("Forbidden", 403)
            
            this_chat.whitelist.append(this_user)
            await self.broadcast_event("approve-join-request", json.dumps({"chatname": quote(chatname), "user": {"name": this_user.name, "pfp": this_user.pfp}}))

            return make_response("OK", 200)

        except (json.JSONDecodeError, KeyError) as e:
            return make_response("Bad Request", 400)
    
    # DELETE /api/chat/:chatname/reject
    async def reject_join(self, request: Request, chatname: str) -> str:
        try:
            chatname = unquote(chatname)
            message_data = json.loads(request.body)
            target = message_data["user"]
            token = message_data["token"]

            this_chat = None
            for chat in self.groups:
                if chat.name == chatname:
                    this_chat = chat
                    break
            if this_chat == None:
                return make_response("Not Found", 404)
            
            this_user = None
            for user in self.users:
                if user.name == target:
                    this_user = user
            if this_user == None:
                return make_response("Not Found", 404)
            
            this_admin = None
            for admin in this_chat.admin:
                if admin.token == token:
                    this_admin = token
            if this_admin == None:
                return make_response("Forbidden", 403)
            
            await self.broadcast_event("reject-join-request", json.dumps({"chatname": quote(chatname), "user": {"name": this_user.name, "pfp": this_user.pfp}}))

            return make_response("OK", 200)

        except (json.JSONDecodeError, KeyError) as e:
            return make_response("Bad Request", 400)

    # DELETE /api/chat/:chatname
    async def remove_user(self, request: Request, chatname: str) -> str:
        try:
            chatname = unquote(chatname)
            message_data = json.loads(request.body)
            user = message_data["user"]
            token = message_data["token"]

            this_chat = None
            for chat in self.groups:
                if chat.name == chatname:
                    this_chat = chat
                    break
            if this_chat == None:
                return make_response("Not Found", 404)
            
            this_user = None
            for user in self.users:
                if user.name == user:
                    this_user = user
            if this_user == None:
                return make_response("Not Found", 404)
            
            this_admin = None
            for admin in this_chat.admin:
                if admin.token == token:
                    this_admin = token
            if this_admin == None:
                return make_response("Forbidden", 403)
            
            if this_chat.public:
                return make_response("Cannot remove user from a public room", 400)

            if this_user not in this_chat.whitelist:
                return make_response("Not Found", 404)
            
            this_chat.whitelist.remove(this_user)
            
            await self.broadcast_event("remove-user", json.dumps({"chatname": quote(chatname), "user": {"name": this_user.name, "pfp": this_user.pfp}}))

            return make_response("OK", 200)

        except (json.JSONDecodeError, KeyError) as e:
            return make_response("Bad Request", 400)

    # GET /api/users
    async def get_users(self, request: Request) -> str:
        return make_response(json.dumps([{"name": user.name, "pfp": user.pfp} for user in self.users]), 200)

    # POST /api/users
    async def register_user(self, request: Request) -> str:
        try:
            message_data = json.loads(request.body)
            user = message_data["user"]
            pfp = message_data["pfp"]
            
            if(user in [user.name for user in self.users]):
                return make_response("Conflict", 409)
            
            token = secrets.token_hex(16)

            self.users.append(User(user, pfp, token))
            
            await self.broadcast_event("register-user", json.dumps({"name": user, "pfp": pfp}))

            return make_response(json.dumps({"token": token}), 201, "application/json")

        except (json.JSONDecodeError, KeyError) as e:
            return make_response("Bad Request", 400)

    # GET /api/events/:token (SSE)
    async def handle_sse(self, loop, client, request: Request, token: str) -> None:

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
            self.sse_clients.discard(client)
            discarded_user = None
            for user in self.users:
                if user.token == token:
                    discarded_user = user
            if(discarded_user != None):
                self.broadcast_event("remove-user", json.dumps({"name": discarded_user.name, "pfp": discarded_user.pfp}))
                self.users.remove(discarded_user)
            client.close()
    
    # SSE methods

    async def broadcast_event(self, event: str, data: str):
        loop = asyncio.get_running_loop()
        msg = f"event: {event}\ndata: {data}\n\n"
        for client in list(self.sse_clients):
            try:
                await loop.sock_sendall(client, msg.encode())
            except (ConnectionResetError, BrokenPipeError):
                pass # Let the heartbeat discard the connection