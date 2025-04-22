def make_response(body: str = "", status: int = 200, content_type: str = "text/plain", is_binary: bool = False) -> bytes:
    reason = {
        200: "OK",
        201: "Created",
        400: "Bad Request",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        500: "Internal Server Error",
        501: "Not Implemented"
    }.get(status, "OK")
    headers = (
        f"HTTP/1.1 {status} {reason}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )

    if is_binary:
        return headers.encode() + body
    else:
        return (headers + body).encode()