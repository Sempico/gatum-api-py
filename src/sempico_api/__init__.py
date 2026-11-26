"""Official Python client for the Sempico Solutions SMS API.

https://api.sempico.solutions/desc/
"""

__version__ = "2.0.0"

from .client import DEFAULT_BASE_URL, AsyncSempicoClient, SempicoClient  # noqa: E402
from .exceptions import (  # noqa: E402
    AuthenticationError,
    BadRequestError,
    PermissionDeniedError,
    SempicoAPIError,
    SempicoConnectionError,
    SempicoError,
)
from .models import (  # noqa: E402
    DeliveryReport,
    DeliveryState,
    ErrorCode,
    MessageType,
    ReplacementResult,
    SendResult,
)
from .webhooks import parse_dlr, verify_api_key  # noqa: E402

__all__ = [
    "__version__",
    "DEFAULT_BASE_URL",
    "SempicoClient",
    "AsyncSempicoClient",
    "SempicoError",
    "SempicoAPIError",
    "SempicoConnectionError",
    "AuthenticationError",
    "PermissionDeniedError",
    "BadRequestError",
    "MessageType",
    "DeliveryState",
    "ErrorCode",
    "SendResult",
    "ReplacementResult",
    "DeliveryReport",
    "parse_dlr",
    "verify_api_key",
]
