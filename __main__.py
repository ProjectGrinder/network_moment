# Import Python Socket api which is abstracted from System Socket API
# This is os independent and can be used in any OS
import socket


from src.start import start
from config import SERVER_CONFIG


def main() -> None:
    start(SERVER_CONFIG["port"])


if __name__ == "__main__":
    main()