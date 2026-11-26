"""Framework-agnostic helpers for receiving delivery reports (DLR)."""

from __future__ import annotations

import hmac
from collections.abc import Mapping
from typing import Any

from .models import DeliveryReport

__all__ = ["parse_dlr", "verify_api_key", "API_KEY_HEADER"]

API_KEY_HEADER = "API_KEY"


def verify_api_key(headers: Mapping[str, Any], expected: str | None) -> bool:
    """Check the ``API_KEY`` header sent with every DLR when a security key is set.

    Returns ``True`` when ``expected`` is empty (no key configured). Uses a
    constant-time comparison. Header lookup is case-insensitive, and also
    accepts ``API-KEY`` because some servers (e.g. nginx, gunicorn) drop or
    rewrite header names that contain an underscore.
    """
    if not expected:
        return True
    lowered = {str(k).lower(): v for k, v in headers.items()}
    received = lowered.get("api_key") or lowered.get("api-key") or lowered.get("http_api_key")
    return received is not None and hmac.compare_digest(str(received), expected)


def parse_dlr(params: Mapping[str, Any]) -> DeliveryReport:
    """Alias of :meth:`DeliveryReport.from_query`."""
    return DeliveryReport.from_query(params)
