from __future__ import annotations

import pytest

from sempico_api import DeliveryReport, DeliveryState

QS = "id_state=598801503&state=DELIVRD&time=2023-07-23+21%3A41%3A20"


def test_fastapi_router():
    pytest.importorskip("fastapi")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from sempico_api.contrib.fastapi import create_dlr_router

    received: list[DeliveryReport] = []

    async def handler(report: DeliveryReport) -> None:
        received.append(report)

    app = FastAPI()
    app.include_router(create_dlr_router(handler, path="/dlr", api_key="k"))
    client = TestClient(app)

    assert client.get(f"/dlr?{QS}").status_code == 403
    resp = client.get(f"/dlr?{QS}", headers={"API_KEY": "k"})
    assert resp.status_code == 200 and resp.text == "598801503"
    assert received[0].state is DeliveryState.DELIVERED
    assert client.get("/dlr?state=x", headers={"API_KEY": "k"}).status_code == 400


def test_flask_extension():
    pytest.importorskip("flask")
    from flask import Flask

    from sempico_api.contrib.flask import Sempico

    app = Flask(__name__)
    app.config["SEMPICO_API_TOKEN"] = "t"
    sempico = Sempico(app)
    received: list[DeliveryReport] = []

    @sempico.dlr_handler("/dlr")
    def on_dlr(report: DeliveryReport) -> None:
        received.append(report)

    resp = app.test_client().get(f"/dlr?{QS}")
    assert resp.status_code == 200 and resp.get_data(as_text=True) == "598801503"
    assert received[0].id_state == 598801503
    with app.app_context():
        assert sempico.client.base_url == "https://api.sempico.solutions"


def test_django_view():
    pytest.importorskip("django")
    import django
    from django.conf import settings

    if not settings.configured:
        settings.configure(SEMPICO={"TOKEN": "t", "DLR_API_KEY": "k"}, ALLOWED_HOSTS=["*"])
        django.setup()
    from django.test import RequestFactory

    from sempico_api.contrib.django import DeliveryReportView, dlr_received

    received: list[DeliveryReport] = []

    def receiver(sender, report, **kwargs):
        received.append(report)

    dlr_received.connect(receiver, weak=False)
    view = DeliveryReportView.as_view()
    rf = RequestFactory()

    assert view(rf.get(f"/dlr?{QS}")).status_code == 403
    resp = view(rf.get(f"/dlr?{QS}", HTTP_API_KEY="k"))
    assert resp.status_code == 200 and resp.content == b"598801503"
    assert received[0].delivered
