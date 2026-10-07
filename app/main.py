"""FastAPI application entrypoint."""

import asyncio
from collections.abc import Awaitable, Callable

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from app.api.routes.todos import router as todos_router
from app.core.config import get_settings

app = FastAPI(title="Team Todo API", version="1.0.0")
settings = get_settings()
request_slots = asyncio.Semaphore(
    settings.database_pool_size + settings.database_max_overflow
)


@app.middleware("http")
async def limit_database_concurrency(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Queue excess requests before they occupy a worker or DB session.

    Returns:
        The downstream HTTP response.

    """
    async with request_slots:
        return await call_next(request)


app.include_router(todos_router)
