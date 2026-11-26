"""Deprecated compatibility shim for code written against ``gatum-api-py`` 1.x.

Use :mod:`sempico_api` instead::

    from sempico_api import SempicoClient
"""

from __future__ import annotations

import warnings
from typing import Any

import httpx

from sempico_api.client import _build_send_params

__all__ = ["GatumAPI"]

warnings.warn(
    "'gatum_api_py' is deprecated, use 'sempico_api' (pip install sempico-api).",
    DeprecationWarning,
    stacklevel=2,
)


class GatumAPI:
    """1.x-compatible client. Returns the raw HTTP response like before."""

    def __init__(self, base_url: str, token: str) -> None:
        self._token = token
        self._url = base_url.rstrip("/") + "/send"

    def send_sms(
        self, phone: str, sender_id: str, text: str, sms_type: str | None = None,
        lifetime: Any = None, begin_date: str | None = None, begin_time: str | None = None,
        delivery: Any = None,
    ) -> httpx.Response:
        params = _build_send_params(
            phone=phone, sender_id=sender_id, text=text, type=sms_type,
            lifetime=int(lifetime) if lifetime is not None else None, send_at=None,
            callback_url=None, delivery=None, shortener=None,
        )
        if begin_date is not None:
            params["beginDate"] = begin_date
        if begin_time is not None:
            params["beginTime"] = begin_time
        if delivery is not None:
            params["delivery"] = (
                ("TRUE" if delivery else "FALSE") if isinstance(delivery, bool) else str(delivery)
            )
        response = httpx.get(self._url, params={"token": self._token, **params}, timeout=30)
        response.raise_for_status()
        return response
