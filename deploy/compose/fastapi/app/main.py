import json


async def app(scope, receive, send):
    if scope["type"] != "http":
        return

    path = scope.get("path", "")
    if path == "/health/livez":
        body = json.dumps({"status": "UP", "service": "fastapi-ai"}).encode("utf-8")
        status = 200
    elif path == "/health/readyz":
        body = json.dumps({"status": "READY", "service": "fastapi-ai"}).encode("utf-8")
        status = 200
    else:
        body = json.dumps({"status": "NOT_FOUND"}).encode("utf-8")
        status = 404

    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [[b"content-type", b"application/json"]],
        }
    )
    await send({"type": "http.response.body", "body": body})
