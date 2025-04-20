import socket
from pprint import pprint


from src.request_factory import RequestFactory
from src.requests.request import Request
from src.api import Api
import asyncio

class Server:

    server:socket
    port_number:int
    api:Api

    def __init__(self, port_number: int) -> None:
        self.port_number = port_number
    
    def start(self) -> None:
        self.server = socket.create_server(
            address=("", self.port_number),
            family=socket.AF_INET
        )
        self.server.setblocking(False)
        self.api = Api()
        
        print("Server listening on port", self.port_number)

        try:
            asyncio.run(self.run_server())
        except KeyboardInterrupt:
            print("Server stopped")
        finally:
            self.server.close()
    
    async def run_server(self):
        loop = asyncio.get_running_loop()

        while True:
            try:
                client, addr = await asyncio.wait_for(loop.sock_accept(self.server), timeout=1.0)
                client.setblocking(False)
                loop.create_task(self.handle_connection(client, addr))
            except Exception as e:
                pprint(f"")

    async def handle_connection(self, client: socket.socket, addr: tuple):
        loop = asyncio.get_running_loop()
        try:
            pprint(f"Connected by {addr}")
            headers, data_part = await self.read_header(client)

            request: Request = RequestFactory(headers.split("\r\n")).create_request()
            request.body += data_part.decode()

            content_length = int(request.header.get_header("Content-Length", "0"))
            current_length = len(request.body.encode())
            while current_length < content_length:
                more = await loop.sock_recv(client, content_length - current_length)
                if not more:
                    break
                request.body += more.decode()
                current_length += len(more)

            if request.path.startswith("/api"):
                await self.api.handle(client, addr, request)
            else:
                # frontend adds routes here later
                response = b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
                await loop.sock_sendall(client, response)
                client.close()

        except Exception as e:
            pprint(f"Error handling {addr}: {e}")
            client.close()


    async def read_header(self, client: socket.socket) -> tuple[str, bytes]:
        loop = asyncio.get_running_loop()
        data = b""
        while True:
            part = await loop.sock_recv(client, 1024)
            if not part:
                break  # Connection closed
            data += part
            if b'\r\n\r\n' in data:
                headers, data = data.split(b'\r\n\r\n', 1)
                break
        return headers.decode('utf-8'), data

    def __del__(self) -> None:
        self.server.close()