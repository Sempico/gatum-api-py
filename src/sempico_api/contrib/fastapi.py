"""FastAPI / Starlette integration.

Install with ``pip install "sempico-api[fastapi]"``.

Example::

    from fastapi import Depends, FastAPI
    from sempico_api import AsyncSempicoClient, DeliveryReport
    from sempico_api.contrib.fastapi import SempicoLifespan, create_dlr_router, get_client

    async def on_dlr(report: DeliveryReport) -> None:
        print(report.id_state, report.state)

    app = FastAPI(lifespan=SempicoLifespan())
    app.include_router(create_dlr_router(on_dlr, path="/sempico/dlr"))

    @app.post("/otp")
    async def otp(phone: str, client: AsyncSempicoClient = Depends(get_client)):
        result = await client.send_sms(phone, "Verify", "Your code: 4542")
        return {"id_state": result.id_state}
"""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from ..client import AsyncSempicoClient
from ..models import DeliveryReport
from ..webhooks import verify_api_key

__all__ = ["SempicoLifespan", "get_client", "create_dlr_router"]

DLRHandler = Callable[[DeliveryReport], Awaitable[None] | None]


class SempicoLifespan:
    """Lifespan that opens one shared :class:`AsyncSempicoClient` per app."""

    def __init__(self, **client_kwargs: Any) -> None:
        self.client_kwargs = client_kwargs

    @asynccontextmanager
    async def __call__(self, app: Any) -> AsyncIterator[None]:
        async with AsyncSempicoClient(**self.client_kwargs) as client:
            app.state.sempico = client
            yield


def get_client(request: Request) -> AsyncSempicoClient:
    """Dependency returning the client created by :class:`SempicoLifespan`."""
    client = getattr(request.app.state, "sempico", None)
    if client is None:
        raise RuntimeError("Add lifespan=SempicoLifespan() to your FastAPI app")
    return client


def create_dlr_router(
    handler: DLRHandler,
    *,
    path: str = "/sempico/dlr",
    api_key: str | None = None,
    **router_kwargs: Any,
) -> APIRouter:
    """Router with a GET endpoint that receives DLRs and answers with ``id_state``.

    Args:
        handler: Sync or async callable receiving a :class:`DeliveryReport`.
        path: Endpoint path; use it as ``callback_url`` or in the Web app settings.
        api_key: Security key from the account settings; checked against the
            ``API_KEY`` header when set.
    """
    router = APIRouter(**router_kwargs)

    @router.get(path, response_class=PlainTextResponse, include_in_schema=False)
    async def receive_dlr(request: Request) -> PlainTextResponse:
        if not verify_api_key(request.headers, api_key):
            raise HTTPException(status_code=403, detail="Invalid API_KEY")
        try:
            report = DeliveryReport.from_query(request.query_params)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        result = handler(report)
        if inspect.isawaitable(result):
            await result
        return PlainTextResponse(report.ack)

    return router
