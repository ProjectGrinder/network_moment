from src.requests.request import Request
from src.requests.request import Header
from src.requests.type import REQUEST_TYPE

class RequestFactory:

    headers: list[str]

    def __init__(self, headers):
        self.headers = headers
    
    def get_request_type(self) -> REQUEST_TYPE:
        match self.headers[0].split(" ")[0]:
            case "GET":
                return REQUEST_TYPE.GET
            case "POST":
                return REQUEST_TYPE.POST
            case "PUT":
                return REQUEST_TYPE.PUT
            case "DELETE":
                return REQUEST_TYPE.DELETE
            case "OPTIONS":
                return REQUEST_TYPE.OPTIONS

    
    def create_request(self) -> Request:
        # Implement Logic to generate Request Object
        header:Header = Header()
        for head in self.headers[1:]:
            key, value = head.split(": ")
            header.add_header(key, value)
        return Request(self.headers[0].split(" ")[1], header, "", self.get_request_type())