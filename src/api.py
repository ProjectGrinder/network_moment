from pprint import pprint

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

    def handle(self, client, addr, request):
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

