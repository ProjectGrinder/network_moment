from src.server import main
import asyncio

def start(port_number: int) -> None:
    asyncio.run(main(port_number))