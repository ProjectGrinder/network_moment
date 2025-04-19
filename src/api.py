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

    def handle(self, client, addr, request: Request):
        pprint("Handling request...")
        if(request.type == REQUEST_TYPE.POST):
            content_length = int(request.header.get_header("Content-Length"))
            while len(request.body) < content_length: # in case of funky long ass data
                chunk = client.recv(1024)
                if not chunk:
                    pprint("Connection closed by client.")
                    break
                request.body += chunk
            pprint("Received request body.")

        pprint(request)
        #Implement Logic for Request

        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 2\r\n"
            "\r\n"
            "OK"
        )

        client.sendall(response.encode())
        client.close()

