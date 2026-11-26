"""Exceptions raised by the Sempico Solutions SMS API client."""

from __future__ import annotations

from typing import Any

__all__ = [
    "SempicoError",
    "SempicoAPIError",
    "AuthenticationError",
    "PermissionDeniedError",
    "BadRequestError",
    "SempicoConnectionError",
]


class SempicoError(Exception):
    """Base class for every error raised by this library."""


class SempicoConnectionError(SempicoError):
    """The API could not be reached (DNS, TLS, timeout, connection reset...)."""


class SempicoAPIError(SempicoError):
    """The API answered with an error.

    Attributes:
        status_code: HTTP status of the response.
        error: The ``error`` value from the JSON body, e.g. ``"no_money"``.
        body: The decoded JSON body (or raw text if it was not JSON).
    """

    def __init__(self, status_code: int, error: str | None, body: Any = None) -> None:
        self.status_code = status_code
        self.error = error
        self.body = body
        super().__init__(f"HTTP {status_code}: {error or 'unknown error'}")


class AuthenticationError(SempicoAPIError):
    """HTTP 401 - the token is wrong or does not belong to an active client."""


class PermissionDeniedError(SempicoAPIError):
    """HTTP 403 - IP not whitelisted, or API is not enabled for the account/tariff."""


class BadRequestError(SempicoAPIError):
    """HTTP 400 - invalid parameters, daily limit, or the SMS was rejected.

    ``error`` holds the machine-readable reason, e.g. ``"incorrect_phone"``,
    ``"no_money"``, ``"blocked_originator"``. See :class:`sempico_api.ErrorCode`.
    """


_STATUS_TO_EXC: dict[int, type[SempicoAPIError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    403: PermissionDeniedError,
}


def error_for_status(status_code: int, error: str | None, body: Any) -> SempicoAPIError:
    return _STATUS_TO_EXC.get(status_code, SempicoAPIError)(status_code, error, body)
