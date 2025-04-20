from pprint import pprint

from src.requests.request import Request
from src.requests.type import REQUEST_TYPE

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

    async def handle(self, client, addr, request: Request):
        # all data is complete from server handling connection and data for api
        pprint(request)
        #Implement Logic for Request

        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Length: 0\r\n"
            "\r\n"
        )

        client.sendall(response.encode())
        client.close()

