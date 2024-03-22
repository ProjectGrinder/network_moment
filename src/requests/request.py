from src.requests.type import REQUEST_TYPE
from src.requests.header import Header


class Request:
    path: str
    header: Header
    body: str
    type: REQUEST_TYPE

    def __init__(self, path: str, header: Header, body: str, type: REQUEST_TYPE) -> None:
        self.path = path
        self.header = header
        self.body = body
        self.type = type
    
    def __str__(self) -> str:
        return f"Path: {self.path}\nType: {self.type}\n{self.header}\nBody: {self.body}"

    def __repr__(self) -> str:
        return f"Path: {self.path}\nType: {self.type}\n{self.header}\nBody: {self.body}"