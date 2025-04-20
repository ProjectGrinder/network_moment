from pprint import pprint
import asyncio
from src.requests.request import Request
from src.requests.type import REQUEST_TYPE
from src.response import make_response

class User:
    name: str
    pfp: int

    def __init__(self, name, pfp):
        self.name = name
        self.pfp = pfp

class Group:
    name: str
    admin: list[User]
    def __init__(self, name, admin):
        self.name = name
        self.admin = admin

class Api:
    users: list[User]
    groups: list[Group]

    def __init__(self):
        self.users = []
        self.groups = []

    async def handle(self, loop: asyncio.AbstractEventLoop, client, addr, request: Request):
        pprint(request)
        
        method = request.type
        path = request.path

        response = None

        if method == REQUEST_TYPE.GET and path == "/api/chat":
            response = await self.get_all_chats(request)

        elif method == REQUEST_TYPE.POST and path.startswith("/api/chat/") and path.count("/") == 3:
            chat_id = path.split("/")[-1]
            response = await self.post_chat_message(request, chat_id)

        elif method == REQUEST_TYPE.POST and path == "/api/chat/create":
            response = await self.create_chat(request)

        elif method == REQUEST_TYPE.GET and path.startswith("/api/chat/") and path.endswith("/join"):
            chat_id = path.split("/")[3]
            response = await self.join_chat(request, chat_id)

        elif method == REQUEST_TYPE.PUT and path.startswith("/api/chat/") and path.count("/") == 3:
            chat_id = path.split("/")[-1]
            response = await self.approve_join(request, chat_id)

        elif method == REQUEST_TYPE.DELETE and path.startswith("/api/chat/") and path.count("/") == 3:
            chat_id = path.split("/")[-1]
            response = await self.remove_user(request, chat_id)

        elif method == REQUEST_TYPE.GET and path == "/api/users":
            response = await self.get_users(request)

        elif method == REQUEST_TYPE.POST and path == "/api/users":
            response = await self.register_user(request)

        elif method == REQUEST_TYPE.GET and path == "/api/events":
            await self.handle_sse(client, request)
            return  # SSE doesn't send a one-shot response — it's streamed

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
        return make_response("Not Implemented", 501)

    # POST /api/chat/:chat_id
    async def post_chat_message(self, request: Request, chat_id: str) -> str:
        return make_response("Not Implemented", 501)

    # POST /api/chat/create
    async def create_chat(self, request: Request) -> str:
        return make_response("Not Implemented", 501)

    # GET /api/chat/:chat_id/join
    async def join_chat(self, request: Request, chat_id: str) -> str:
        return make_response("Not Implemented", 501)

    # PUT /api/chat/:chat_id
    async def approve_join(self, request: Request, chat_id: str) -> str:
        return make_response("Not Implemented", 501)

    # DELETE /api/chat/:chat_id
    async def remove_user(self, request: Request, chat_id: str) -> str:
        return make_response("Not Implemented", 501)

    # GET /api/users
    async def get_users(self, request: Request) -> str:
        return make_response("Not Implemented", 501)

    # POST /api/users
    async def register_user(self, request: Request) -> str:
        return make_response("Not Implemented", 501)

    # GET /api/events (SSE)
    async def handle_sse(self, client, request: Request) -> None:
        # SSE doesn't return a one-shot response, it's a stream
        pass