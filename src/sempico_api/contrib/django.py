"""Django integration.

Install with ``pip install "sempico-api[django]"``.

settings.py::

    SEMPICO = {
        "TOKEN": env("SEMPICO_API_TOKEN"),
        "BASE_URL": "https://api.sempico.solutions",  # optional
        "DLR_API_KEY": env("SEMPICO_DLR_API_KEY", default=None),  # optional
    }

urls.py::

    from sempico_api.contrib.django import DeliveryReportView
    urlpatterns = [path("sempico/dlr/", DeliveryReportView.as_view())]

Anywhere (e.g. receivers.py)::

    from django.dispatch import receiver
    from sempico_api.contrib.django import dlr_received, get_client

    @receiver(dlr_received)
    def on_dlr(sender, report, **kwargs):
        Message.objects.filter(id_state=report.id_state).update(state=report.state)

    get_client().send_sms("380501234567", "Verify", "Your code: 4542")
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from django.conf import settings
from django.dispatch import Signal
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from ..client import SempicoClient
from ..models import DeliveryReport
from ..webhooks import verify_api_key

__all__ = ["get_client", "dlr_received", "DeliveryReportView"]

#: Sent for every valid DLR with ``report=DeliveryReport``.
dlr_received = Signal()


def _config() -> dict[str, Any]:
    return getattr(settings, "SEMPICO", {})


@lru_cache(maxsize=1)
def get_client() -> SempicoClient:
    """Process-wide client configured from ``settings.SEMPICO``."""
    cfg = _config()
    return SempicoClient(token=cfg.get("TOKEN"), base_url=cfg.get("BASE_URL"))


@method_decorator(csrf_exempt, name="dispatch")
class DeliveryReportView(View):
    """Receives DLRs, emits :data:`dlr_received` and answers with ``id_state``."""

    http_method_names = ["get"]

    def get(self, request: HttpRequest) -> HttpResponse:
        if not verify_api_key(request.headers, _config().get("DLR_API_KEY")):
            return HttpResponseForbidden("Invalid API_KEY")
        try:
            report = DeliveryReport.from_query(request.GET)
        except ValueError as exc:
            return HttpResponseBadRequest(str(exc))
        dlr_received.send(sender=self.__class__, report=report)
        return HttpResponse(report.ack, content_type="text/plain")
