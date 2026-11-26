"""Deprecated: ``gatum-api-py`` is now ``sempico-api``.

This package keeps code written for 1.0.x working unchanged. New code should use::

    from sempico_api import SempicoClient

See https://github.com/Sempico/gatum-api-py#migrating-from-gatum-api-py-1x
"""

import warnings

from .GatumAPI import GatumAPI

__version__ = "1.1.0"
__all__ = ["GatumAPI"]

warnings.warn(
    "'gatum-api-py' has been renamed to 'sempico-api' and will get no further updates. "
    "Replace 'from gatum_api_py import GatumAPI' with "
    "'from sempico_api import SempicoClient' (already installed as a dependency).",
    FutureWarning,  # shown by default, unlike DeprecationWarning from a library
    stacklevel=2,
)
