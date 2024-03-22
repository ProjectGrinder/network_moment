from src.server import Server


def start(port_number: int) -> None:
    Server(port_number).start()