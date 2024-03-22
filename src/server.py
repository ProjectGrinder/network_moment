import socket
from pprint import pprint


from src.request_factory import RequestFactory
from src.requests.request import Request


class Server:

    server:socket
    port_number:int

    def __init__(self, port_number: int) -> None:
        self.port_number = port_number
    
    def start(self) -> None:
        self.server = socket.create_server(
            address=("", self.port_number),
            family=socket.AF_INET
        )
        self.server.settimeout(1.0)
        while True:
            # Read first 1024 bytes to get headers
            try:
                client, addr = self.server.accept()
                pprint(f"Connected by {addr}")
                headers = self.read_header(client)
                # Generate Request object
                request: Request = RequestFactory(headers.split("\r\n")).create_request()
                pprint(request)
                #Implement Logic for Request
            except TimeoutError:
                continue
            except KeyboardInterrupt:
                print("Server Stopped")
                break
    
    def read_header(self, client:any) -> str:
        data = b""
        # Read first 1024 bytes to get headers
        while True:
            part = client.recv(1024)
            data += part
            if b'\r\n\r\n' in data:
                headers, data = data.split(b'\r\n\r\n', 1)
                break
        return headers.decode('utf-8')

    def __del__(self) -> None:
        self.server.close()