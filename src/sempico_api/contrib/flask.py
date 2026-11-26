"""Flask integration.

Install with ``pip install "sempico-api[flask]"``.

Config keys: ``SEMPICO_API_TOKEN``, ``SEMPICO_BASE_URL``, ``SEMPICO_DLR_API_KEY``.

Example::

    from flask import Flask
    from sempico_api.contrib.flask import Sempico

    app = Flask(__name__)
    app.config["SEMPICO_API_TOKEN"] = "..."
    sempico = Sempico(app)

    @sempico.dlr_handler("/sempico/dlr")
    def on_dlr(report):
        print(report.id_state, report.state)

    @app.post("/otp")
    def otp():
        result = sempico.client.send_sms("380501234567", "Verify", "Your code: 4542")
        return {"id_state": result.id_state}
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from flask import Flask, abort, current_app, request

from ..client import SempicoClient
from ..models import DeliveryReport
from ..webhooks import verify_api_key

__all__ = ["Sempico"]

_EXT = "sempico"


class Sempico:
    """Flask extension holding a shared :class:`SempicoClient`."""

    def __init__(self, app: Flask | None = None, **client_kwargs: Any) -> None:
        self.client_kwargs = client_kwargs
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        client = SempicoClient(
            token=app.config.get("SEMPICO_API_TOKEN"),
            base_url=app.config.get("SEMPICO_BASE_URL"),
            **self.client_kwargs,
        )
        app.extensions[_EXT] = client
        self._app = app

    @property
    def client(self) -> SempicoClient:
        return current_app.extensions[_EXT]

    def dlr_handler(
        self, rule: str = "/sempico/dlr", **route_kwargs: Any
    ) -> Callable[[Callable[[DeliveryReport], Any]], Callable[[DeliveryReport], Any]]:
        """Register a GET endpoint for DLRs; the decorated function gets a report."""

        def decorator(func: Callable[[DeliveryReport], Any]) -> Callable[[DeliveryReport], Any]:
            def view() -> tuple[str, int]:
                expected = current_app.config.get("SEMPICO_DLR_API_KEY")
                if not verify_api_key(request.headers, expected):
                    abort(403)
                try:
                    report = DeliveryReport.from_query(request.args)
                except ValueError:
                    abort(400)
                func(report)
                return report.ack, 200

            self._app.add_url_rule(
                rule, endpoint=f"sempico_dlr_{func.__name__}", view_func=view,
                methods=["GET"], **route_kwargs,
            )
            return func

        return decorator
