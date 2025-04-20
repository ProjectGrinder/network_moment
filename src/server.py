import socket
from pprint import pprint


from src.requests.type import REQUEST_TYPE
from src.request_factory import RequestFactory
from src.response import make_response
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
            except TimeoutError:
                pass
            except Exception as e:
                pprint(f"")

    async def handle_connection(self, client: socket.socket, addr: tuple):
        loop = asyncio.get_running_loop()
        try:
            pprint(f"Connected by {addr}")
            headers, data_part = await self.read_header(client)

            request: Request = RequestFactory(headers.split("\r\n")).create_request()
            request.body += data_part.decode()

            if request.type in [REQUEST_TYPE.POST, REQUEST_TYPE.PUT]:
                content_length = request.header.get_header("Content-Length")

                if content_length is None:
                    response = make_response("Bad Request", 400)
                    await loop.sock_sendall(client, response.encode())
                    client.close()
                    return
                
                try:
                    content_length = int(content_length)
                except ValueError:
                    response = make_response("Bad Request", 400)
                    await loop.sock_sendall(client, response.encode())
                    client.close()
                    return 

                current_length = len(request.body.encode())
                while current_length < content_length:
                    more = await loop.sock_recv(client, content_length - current_length)
                    if not more:
                        break
                    request.body += more.decode()
                    current_length += len(more)

            if request.path.startswith("/api"):
                await self.api.handle(loop, client, addr, request)
            else:
                # frontend adds routes here later (or can be added to api, i guess)
                response = make_response("Not Found",status=404)
                await loop.sock_sendall(client, response)
                client.close()
            return

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