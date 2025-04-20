def make_response(body: str = "", status: int = 200, content_type: str = "text/plain") -> str:
    reason = {
        200: "OK",
        201: "Created",
        400: "Bad Request",
        404: "Not Found",
        409: "Conflict",
        500: "Internal Server Error",
        501: "Not Implemented"
    }.get(status, "OK")
    return (
        f"HTTP/1.1 {status} {reason}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body.encode())}\r\n"
        f"\r\n"
        f"{body}"
    )