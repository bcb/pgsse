"""Listen for Postgres notifications and send them as Server-Sent Events."""
import asyncio
import json
import os
from typing import Any, AsyncGenerator, Generator

import psycopg2  # type: ignore
import psycopg2.extensions  # type: ignore
from fastapi import Depends, FastAPI, Request
from fastapi.responses import StreamingResponse

app: FastAPI = FastAPI()


def get_db() -> Generator[Any, None, None]:
    db = psycopg2.connect(os.environ["POSTGRES_URI"])
    # Listening doesn't work without this, but no explanation why in psycopg2 docs
    db.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        yield db
    finally:
        db.close()


def sse(value: str) -> str:
    """
    Takes a string, potentially containing a json object, and returns an SSE event
    message.

    Args:
        value: Should be either a JSON encoded string, containing "data" and optionally
            "event", or anything else to send a comment.

    Examples:
        sse({"data": 1})
        sse({"event": "", "data": 1})
        sse("This is a comment")
    """
    try:
        deserialized = json.loads(value)
    except json.decoder.JSONDecodeError:
        return f": {value}\n\n"
    else:
        return (
            f"event: {deserialized['event']}\ndata: {deserialized['data']}\n\n"
            if "event" in deserialized
            else f"data: {deserialized['data']}\n\n"
        )


async def event_stream(
    request: Request, db: Any, channel: str, last_event_id: str
) -> AsyncGenerator[str, None]:
    # Send an initial message to ping the client, because it doesn't get the onopen
    # event until receiving an event.
    yield sse("Heartbeat")
    last_heartbeat = asyncio.get_running_loop().time()
    db.cursor().execute(f'LISTEN "{channel}";')
    while True:
        if await request.is_disconnected():
            break
        db.poll()
        while db.notifies:
            yield sse(db.notifies.pop(0).payload)
            last_heartbeat = asyncio.get_running_loop().time()
        if asyncio.get_running_loop().time() >= last_heartbeat + 25:
            yield sse("Heartbeat")
            last_heartbeat = asyncio.get_running_loop().time()
        # await asyncio.sleep(0.001)


@app.get("/{channel}")  # Should also receive token
async def events(channel: str, request: Request, db: Any = Depends(get_db)) -> None:
    await StreamingResponse(
        event_stream(request, db, channel, request.headers.get("Last-Event-ID", "")),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-transform"},
    )(request.scope, request.receive, request._send)
