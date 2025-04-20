from pprint import pprint

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
    routes: dict[str, any]

    def __init__(self):
        self.users = []
        self.groups = []

    async def handle(self, client, addr, request: Request):
        pprint(request)
        response = make_response("OK")
        client.sendall(response.encode())
        client.close()

