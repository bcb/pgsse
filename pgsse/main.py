"""Listens for Postgres notifications, passes them through as Server-Sent Events."""
import asyncio
import json
import os
import select
from typing import Any, AsyncGenerator, Generator, Optional

from fastapi import Depends, FastAPI, Request
from fastapi.responses import StreamingResponse
import psycopg2  # type: ignore
import psycopg2.extensions  # type: ignore

app: FastAPI = FastAPI()


def get_db() -> Generator[Any, None, None]:
    db = psycopg2.connect(os.environ["POSTGRES_URL"])
    # Listening doesn't work without this, but no explanation why in psycopg2 docs
    db.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        yield db
    finally:
        db.close()


def sse(*, type: str, data: Optional[str] = None, id: int = 0) -> str:
    return f"event: {type}\ndata: {data}\nid: {id}\n\n"


async def event_stream(
    request: Request, db: Any, channel: str, last_event_id: int
) -> AsyncGenerator[str, None]:
    # Send an initial message to ping the client, because it doesn't get the onopen
    # event until receiving an event.
    yield sse(type="heartbeat")
    last_heartbeat = asyncio.get_running_loop().time()
    db.cursor().execute(f'LISTEN "{channel}";')
    while True:
        if await request.is_disconnected():
            break
        db.poll()
        while db.notifies:
            payload = json.loads(db.notifies.pop(0).payload)
            yield sse(type=payload[0], data=json.dumps(payload[1]))
            last_heartbeat = asyncio.get_running_loop().time()
        if asyncio.get_running_loop().time() >= last_heartbeat + 25:
            yield sse(type="heartbeat")
            last_heartbeat = asyncio.get_running_loop().time()
        await asyncio.sleep(0.001)


@app.get("/{channel}")  # Should also receive token
async def events(channel: str, request: Request, db: Any = Depends(get_db)) -> None:
    await StreamingResponse(
        event_stream(request, db, channel, request.headers.get("Last-Event-ID", 0)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-transform"},
    )(request.scope, request.receive, request._send)
