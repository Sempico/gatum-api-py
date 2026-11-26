"""Typed request/response models for the Sempico Solutions SMS API."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

__all__ = [
    "MessageType",
    "DeliveryState",
    "ErrorCode",
    "SendResult",
    "ReplacementResult",
    "DeliveryReport",
]


class MessageType(str, Enum):
    """Value of the ``type`` parameter of ``/send``."""

    SMS = "SMS"
    FLASHSMS = "FLASHSMS"
    WAPPUSH = "WAPPUSH"
    VCARD = "VCARD"
    HLR = "HLR"
    MNP = "MNP"


class DeliveryState(str, Enum):
    """``state`` value of a delivery report (DLR)."""

    DELIVERED = "DELIVRD"
    UNDELIVERED = "UNDELIV"
    EXPIRED = "EXPIRED"
    ENROUTE = "ENROUTE"

    @property
    def is_final(self) -> bool:
        return self is not DeliveryState.ENROUTE


class ErrorCode(str, Enum):
    """Machine-readable reasons returned by ``/send`` with HTTP 400."""

    INCORRECT_PHONE = "incorrect_phone"
    INCORRECT_PHONE_LENGTH = "incorrect_phone_length"
    NO_MCC_MNC = "no_mcc_mnc"
    PHONE_IN_BLACK_LIST = "phone_in_black_list"
    NO_ACTIVE_AGGREGATOR = "no_active_aggregator"
    NO_SOURCE_PRICE = "no_source_price"
    NO_CLIENT_PRICE = "no_client_price"
    NO_MONEY = "no_money"
    BLOCKED_ORIGINATOR = "blocked_originator"
    BLOCKED_SHORTENER_RULE = "blocked_shortener_rule"
    UNDEFINED_CODE = "undefined_code"


@dataclass(frozen=True, slots=True)
class SendResult:
    """Result of ``/send``.

    ``id_states`` has one ID per SMS part; a single-part SMS has exactly one.
    Store these IDs to match incoming delivery reports.
    """

    phone: str
    id_states: tuple[int, ...]
    raw: Mapping[str, Any] = field(repr=False, compare=False)

    @property
    def id_state(self) -> int:
        """ID of the first (or only) part."""
        return self.id_states[0]

    @property
    def parts(self) -> int:
        return len(self.id_states)

    @classmethod
    def from_response(cls, data: Mapping[str, Any]) -> SendResult:
        phone, value = next(iter(data.items()))
        if isinstance(value, list):
            ids = tuple(int(p["id_state"] if isinstance(p, Mapping) else p) for p in value)
        else:
            ids = (int(value),)
        return cls(phone=str(phone), id_states=ids, raw=data)


@dataclass(frozen=True, slots=True)
class ReplacementResult:
    """Result of ``/replacement``: how the platform would rewrite the SMS."""

    phone: str
    status: bool
    error: str | None
    content: str | None
    sender: str | None
    parts: int | None
    mcc: str | None
    mnc: str | None
    raw: Mapping[str, Any] = field(repr=False, compare=False)

    @classmethod
    def from_response(cls, data: Mapping[str, Any]) -> ReplacementResult:
        phone, value = next(iter(data.items()))
        rep = value.get("replacing") or {}
        parts = rep.get("parts")
        return cls(
            phone=str(phone),
            status=bool(value.get("status")),
            error=value.get("error"),
            content=rep.get("replacingContent"),
            sender=rep.get("replacingSender"),
            parts=int(parts) if parts is not None else None,
            mcc=rep.get("MCC"),
            mnc=rep.get("MNC"),
            raw=data,
        )


@dataclass(frozen=True, slots=True)
class DeliveryReport:
    """A delivery report (DLR) received on your ``callback_url``.

    Build it from the query string of the incoming GET request with
    :meth:`from_query`; it works with any framework's query-params mapping.
    """

    id_state: int
    state: DeliveryState | str
    time: datetime | None
    error: str | None = None
    hlr: Mapping[str, str] = field(default_factory=dict)

    @property
    def delivered(self) -> bool:
        return self.state is DeliveryState.DELIVERED

    @property
    def ack(self) -> str:
        """Body to answer with when the confirmation mode is enabled."""
        return str(self.id_state)

    @classmethod
    def from_query(cls, params: Mapping[str, Any]) -> DeliveryReport:
        """Parse DLR query parameters.

        Raises:
            ValueError: if ``id_state`` or ``state`` is missing/invalid.
        """
        try:
            id_state = int(params["id_state"])
            raw_state = str(params["state"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("DLR request must contain 'id_state' and 'state'") from exc

        try:
            state: DeliveryState | str = DeliveryState(raw_state)
        except ValueError:
            state = raw_state  # forward-compatible with new states

        raw_time = params.get("time")
        parsed_time: datetime | None = None
        if raw_time:
            try:
                parsed_time = datetime.fromisoformat(str(raw_time))
            except ValueError:
                parsed_time = None

        error = params.get("error")
        hlr = {
            key[4:-1]: str(value)
            for key, value in params.items()
            if key.startswith("hlr[") and key.endswith("]")
        }
        return cls(
            id_state=id_state,
            state=state,
            time=parsed_time,
            error=str(error) if error not in (None, "", "0") else None,
            hlr=hlr,
        )
