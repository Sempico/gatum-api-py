"""1.0.x-compatible client for the Sempico Solutions GET API (deprecated)."""

from __future__ import annotations

import urllib.parse
from typing import Any

import requests

DEFAULT_TIMEOUT = 30


class GatumAPI:
    """Deprecated: use :class:`sempico_api.SempicoClient` instead.

    The signature and return type are the same as in 1.0.x: ``send_sms`` returns
    a ``requests.Response`` and raises ``requests.HTTPError`` on HTTP errors.
    """

    def __init__(self, base_url: str, token: str, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.__token = token
        self.__send_sms_path = base_url.rstrip("/") + "/send?"
        self.__timeout = timeout
        self.__headers = {"accept": "application/json"}

    def __repr__(self) -> str:
        return f"GatumAPI(send_url={self.__send_sms_path[:-1]!r})"

    def send_sms(
        self,
        phone: str,
        sender_id: str,
        text: str,
        sms_type: str | None = None,
        lifetime: Any = None,
        begin_date: str | None = None,
        begin_time: str | None = None,
        delivery: Any = None,
    ) -> requests.Response:
        params: dict[str, Any] = {
            "token": self.__token,
            "phone": phone,
            "senderID": sender_id,
            "text": text,
        }
        if sms_type is not None:
            params["type"] = sms_type
        if lifetime is not None:
            params["lifetime"] = lifetime
        if begin_date is not None:
            params["beginDate"] = begin_date
        if begin_time is not None:
            params["beginTime"] = begin_time
        if delivery is not None:
            # 1.0.x sent Python bools as "True"/"False"; the API expects TRUE/FALSE.
            params["delivery"] = (
                ("TRUE" if delivery else "FALSE") if isinstance(delivery, bool) else delivery
            )
        return self._make_request(path=self.__send_sms_path, params=params)

    def _make_request(self, path: str, params: dict[str, Any]) -> requests.Response:
        full_url = path + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        response = requests.get(full_url, headers=self.__headers, timeout=self.__timeout)
        response.raise_for_status()
        return response
