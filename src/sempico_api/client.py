"""Sync and async clients for the Sempico Solutions SMS HTTP API."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from types import TracebackType
from typing import Any

import httpx

from . import __version__
from .exceptions import SempicoConnectionError, error_for_status
from .models import MessageType, ReplacementResult, SendResult

__all__ = ["SempicoClient", "AsyncSempicoClient", "DEFAULT_BASE_URL"]

DEFAULT_BASE_URL = "https://api.sempico.solutions"
DEFAULT_TIMEOUT = 30.0
TOKEN_ENV = "SEMPICO_API_TOKEN"
BASE_URL_ENV = "SEMPICO_BASE_URL"


def _resolve_config(token: str | None, base_url: str | None) -> tuple[str, str]:
    token = token or os.environ.get(TOKEN_ENV)
    if not token:
        raise ValueError(f"API token is required: pass token=... or set {TOKEN_ENV}")
    base_url = (base_url or os.environ.get(BASE_URL_ENV) or DEFAULT_BASE_URL).rstrip("/")
    if not base_url.startswith("https://"):
        # The token travels in the query string - never send it over plain HTTP.
        raise ValueError("base_url must use https://")
    return token, base_url


def _build_send_params(
    *,
    phone: str,
    sender_id: str,
    text: str,
    type: MessageType | str | None,
    lifetime: int | timedelta | None,
    send_at: datetime | None,
    callback_url: str | None,
    delivery: bool | None,
    shortener: str | None,
) -> dict[str, str]:
    params: dict[str, str] = {"phone": str(phone), "senderID": sender_id, "text": text}
    if type is not None:
        params["type"] = type.value if isinstance(type, MessageType) else str(type)
    if lifetime is not None:
        seconds = lifetime.total_seconds() if isinstance(lifetime, timedelta) else lifetime
        params["lifetime"] = str(int(seconds))
    if send_at is not None:
        # The API expects GMT+0. Naive datetimes are treated as UTC.
        if send_at.tzinfo is not None:
            send_at = send_at.astimezone(timezone.utc)
        params["beginDate"] = send_at.strftime("%Y-%m-%d")
        params["beginTime"] = send_at.strftime("%H:%M:%S")
    if callback_url is not None:
        params["callback_url"] = callback_url
    if delivery is not None:
        params["delivery"] = "TRUE" if delivery else "FALSE"
    if shortener is not None:
        params["shortener"] = shortener
    return params


def _handle(response: httpx.Response) -> Any:
    try:
        body: Any = response.json()
    except ValueError:
        body = response.text
    if response.is_success and isinstance(body, dict) and body and "error" not in body:
        return body
    error = body.get("error") if isinstance(body, dict) else None
    if error is None and isinstance(body, dict) and body:
        # /replacement returns {"<phone>": {"status": false, "error": "..."}}
        first = next(iter(body.values()))
        if isinstance(first, dict):
            error = first.get("error")
    raise error_for_status(response.status_code, error, body)


class _Base:
    def __init__(
        self,
        token: str | None,
        base_url: str | None,
        timeout: float | httpx.Timeout,
    ) -> None:
        self._token, self.base_url = _resolve_config(token, base_url)
        self._client_kwargs: dict[str, Any] = {
            "base_url": self.base_url,
            "timeout": timeout,
            "headers": {
                "Accept": "application/json",
                "User-Agent": f"sempico-api-python/{__version__}",
            },
        }

    def __repr__(self) -> str:  # never leak the token
        return f"{type(self).__name__}(base_url={self.base_url!r})"

    def _auth(self, params: dict[str, str]) -> dict[str, str]:
        return {"token": self._token, **params}


class SempicoClient(_Base):
    """Synchronous client.

    Example::

        from sempico_api import SempicoClient

        with SempicoClient(token="...") as client:
            result = client.send_sms(phone="380501234567", sender_id="Verify", text="Code: 4542")
            print(result.id_state)

    Args:
        token: API token from the Web app. Defaults to ``$SEMPICO_API_TOKEN``.
        base_url: API host. Defaults to ``$SEMPICO_BASE_URL`` or
            ``https://api.sempico.solutions``. White-label partners pass their own host.
        timeout: Request timeout in seconds.
        retries: Retries on *connection* failures only. Requests that reached the
            server are never retried, so an SMS cannot be sent twice.
        http_client: Bring your own configured ``httpx.Client`` (proxies, mTLS...).
    """

    def __init__(
        self,
        token: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float | httpx.Timeout = DEFAULT_TIMEOUT,
        retries: int = 2,
        http_client: httpx.Client | None = None,
    ) -> None:
        super().__init__(token, base_url, timeout)
        self._owns_client = http_client is None
        self._http = http_client or httpx.Client(
            transport=httpx.HTTPTransport(retries=retries), **self._client_kwargs
        )

    def _get(self, path: str, params: dict[str, str]) -> Any:
        try:
            response = self._http.get(self.base_url + path, params=self._auth(params))
        except httpx.TransportError as exc:
            raise SempicoConnectionError(str(exc)) from exc
        return _handle(response)

    def send_sms(
        self,
        phone: str,
        sender_id: str,
        text: str,
        *,
        type: MessageType | str | None = None,
        lifetime: int | timedelta | None = None,
        send_at: datetime | None = None,
        callback_url: str | None = None,
        delivery: bool | None = None,
        shortener: str | None = None,
    ) -> SendResult:
        """Send one SMS (or an HLR/MNP request with ``type=``).

        Args:
            phone: Number in international format, e.g. ``"380501234567"``.
            sender_id: Numeric (3-15 digits) or alphanumeric (<= 11 chars) sender.
            text: Message text. Long texts are split into parts by the platform.
            type: :class:`MessageType`; ``SMS`` by default.
            lifetime: How long to try delivering (seconds or ``timedelta``); 86400 by default.
            send_at: Scheduled send time. Converted to UTC; naive values are UTC.
            callback_url: Per-message DLR webhook; overrides the account setting.
            delivery: Whether DLRs are sent (``True`` by default on the server).
            shortener: URL-shortener settings for links in the text.

        Raises:
            BadRequestError: the SMS was rejected; see ``exc.error``.
            AuthenticationError, PermissionDeniedError, SempicoConnectionError.
        """
        params = _build_send_params(
            phone=phone, sender_id=sender_id, text=text, type=type, lifetime=lifetime,
            send_at=send_at, callback_url=callback_url, delivery=delivery, shortener=shortener,
        )
        return SendResult.from_response(self._get("/send", params))

    def hlr_lookup(self, phone: str, sender_id: str = "HLR", **kwargs: Any) -> SendResult:
        """Request an HLR lookup. The result arrives in the DLR ``hlr[...]`` fields."""
        return self.send_sms(phone, sender_id, text="HLR", type=MessageType.HLR, **kwargs)

    def mnp_lookup(self, phone: str, sender_id: str = "MNP", **kwargs: Any) -> SendResult:
        """Request an MNP (number portability) lookup."""
        return self.send_sms(phone, sender_id, text="MNP", type=MessageType.MNP, **kwargs)

    def check_replacement(self, phone: str, sender_id: str, text: str) -> ReplacementResult:
        """Preview how routing rules would rewrite sender/text, without sending."""
        data = self._get("/replacement", {"phone": str(phone), "senderID": sender_id, "text": text})
        return ReplacementResult.from_response(data)

    def close(self) -> None:
        if self._owns_client:
            self._http.close()

    def __enter__(self) -> SempicoClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class AsyncSempicoClient(_Base):
    """Asynchronous client with the same API as :class:`SempicoClient`.

    Example::

        async with AsyncSempicoClient() as client:
            result = await client.send_sms("380501234567", "Verify", "Code: 4542")
    """

    def __init__(
        self,
        token: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float | httpx.Timeout = DEFAULT_TIMEOUT,
        retries: int = 2,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(token, base_url, timeout)
        self._owns_client = http_client is None
        self._http = http_client or httpx.AsyncClient(
            transport=httpx.AsyncHTTPTransport(retries=retries), **self._client_kwargs
        )

    async def _get(self, path: str, params: dict[str, str]) -> Any:
        try:
            response = await self._http.get(self.base_url + path, params=self._auth(params))
        except httpx.TransportError as exc:
            raise SempicoConnectionError(str(exc)) from exc
        return _handle(response)

    async def send_sms(
        self,
        phone: str,
        sender_id: str,
        text: str,
        *,
        type: MessageType | str | None = None,
        lifetime: int | timedelta | None = None,
        send_at: datetime | None = None,
        callback_url: str | None = None,
        delivery: bool | None = None,
        shortener: str | None = None,
    ) -> SendResult:
        """See :meth:`SempicoClient.send_sms`."""
        params = _build_send_params(
            phone=phone, sender_id=sender_id, text=text, type=type, lifetime=lifetime,
            send_at=send_at, callback_url=callback_url, delivery=delivery, shortener=shortener,
        )
        return SendResult.from_response(await self._get("/send", params))

    async def hlr_lookup(self, phone: str, sender_id: str = "HLR", **kwargs: Any) -> SendResult:
        return await self.send_sms(phone, sender_id, text="HLR", type=MessageType.HLR, **kwargs)

    async def mnp_lookup(self, phone: str, sender_id: str = "MNP", **kwargs: Any) -> SendResult:
        return await self.send_sms(phone, sender_id, text="MNP", type=MessageType.MNP, **kwargs)

    async def check_replacement(self, phone: str, sender_id: str, text: str) -> ReplacementResult:
        data = await self._get(
            "/replacement", {"phone": str(phone), "senderID": sender_id, "text": text}
        )
        return ReplacementResult.from_response(data)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._http.aclose()

    async def __aenter__(self) -> AsyncSempicoClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()
