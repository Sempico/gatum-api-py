from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from sempico_api import (
    AsyncSempicoClient,
    AuthenticationError,
    BadRequestError,
    DeliveryReport,
    DeliveryState,
    ErrorCode,
    MessageType,
    PermissionDeniedError,
    SempicoClient,
    SempicoConnectionError,
    verify_api_key,
)

BASE = "https://api.example.test"


def make_client(handler, cls=SempicoClient):
    transport_cls = httpx.MockTransport
    http_cls = httpx.Client if cls is SempicoClient else httpx.AsyncClient
    http = http_cls(transport=transport_cls(handler))
    return cls(token="secret", base_url=BASE, http_client=http)


def json_response(status: int, body) -> httpx.Response:
    return httpx.Response(
        status, content=json.dumps(body), headers={"content-type": "application/json"}
    )


def test_send_sms_single_part_and_params():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = request.url
        return json_response(200, {"380501234567": 1855153903})

    client = make_client(handler)
    result = client.send_sms(
        "380501234567", "Verify", "Код: 4542 & more",
        type=MessageType.FLASHSMS,
        lifetime=timedelta(hours=1),
        send_at=datetime(2026, 1, 2, 5, 4, 3, tzinfo=timezone(timedelta(hours=2))),
        callback_url="https://x.test/dlr?a=1",
        delivery=False,
    )
    assert result.phone == "380501234567"
    assert result.id_state == 1855153903
    assert result.parts == 1

    q = seen["url"].params
    assert seen["url"].path == "/send"
    assert q["token"] == "secret"
    assert q["senderID"] == "Verify"
    assert q["text"] == "Код: 4542 & more"
    assert q["type"] == "FLASHSMS"
    assert q["lifetime"] == "3600"
    assert q["beginDate"] == "2026-01-02"
    assert q["beginTime"] == "03:04:03"  # converted to UTC
    assert q["callback_url"] == "https://x.test/dlr?a=1"
    assert q["delivery"] == "FALSE"


def test_send_sms_multi_part():
    body = {"380501234567": [{"id_state": 1}, {"id_state": 2}]}
    client = make_client(lambda r: json_response(200, body))
    result = client.send_sms("380501234567", "SMS", "long")
    assert result.id_states == (1, 2)
    assert result.parts == 2


@pytest.mark.parametrize(
    ("status", "error", "exc"),
    [
        (400, "no_money", BadRequestError),
        (401, "Incorrect token", AuthenticationError),
        (403, "IP is not in WhiteList", PermissionDeniedError),
    ],
)
def test_errors(status, error, exc):
    client = make_client(lambda r: json_response(status, {"error": error}))
    with pytest.raises(exc) as info:
        client.send_sms("1", "SMS", "x")
    assert info.value.error == error
    assert info.value.status_code == status


def test_error_code_enum_compares_with_str():
    client = make_client(lambda r: json_response(400, {"error": "no_money"}))
    with pytest.raises(BadRequestError) as info:
        client.send_sms("1", "SMS", "x")
    assert info.value.error == ErrorCode.NO_MONEY


def test_connection_error():
    def handler(request):
        raise httpx.ConnectError("boom", request=request)

    with pytest.raises(SempicoConnectionError):
        make_client(handler).send_sms("1", "SMS", "x")


def test_replacement():
    body = {
        "12345678910": {
            "status": True,
            "error": None,
            "replacing": {
                "replacingContent": "Hello everybody!",
                "replacingSender": "SMS",
                "parts": "1",
                "MCC": "310",
                "MNC": "0",
            },
        }
    }
    client = make_client(lambda req: json_response(200, body))
    r = client.check_replacement("12345678910", "SMS", "Hi")
    assert r.status is True and r.content == "Hello everybody!" and r.parts == 1 and r.mcc == "310"


def test_replacement_rejected():
    body = {"1": {"status": False, "error": "no_client_price", "replacing": None}}
    with pytest.raises(BadRequestError) as info:
        make_client(lambda req: json_response(400, body)).check_replacement("1", "SMS", "Hi")
    assert info.value.error == "no_client_price"


def test_hlr_lookup_sets_type():
    seen = {}

    def handler(request):
        seen["type"] = request.url.params["type"]
        return json_response(200, {"1": 5})

    make_client(handler).hlr_lookup("1")
    assert seen["type"] == "HLR"


def test_token_required(monkeypatch):
    monkeypatch.delenv("SEMPICO_API_TOKEN", raising=False)
    with pytest.raises(ValueError):
        SempicoClient()


def test_token_from_env_and_repr_hides_it(monkeypatch):
    monkeypatch.setenv("SEMPICO_API_TOKEN", "envtoken")
    client = SempicoClient()
    assert "envtoken" not in repr(client)
    client.close()


def test_http_base_url_rejected():
    with pytest.raises(ValueError):
        SempicoClient(token="t", base_url="http://insecure.test")


async def test_async_client():
    async with make_client(lambda r: json_response(200, {"1": 7}), cls=AsyncSempicoClient) as c:
        result = await c.send_sms("1", "SMS", "x")
    assert result.id_state == 7


def test_dlr_parsing():
    report = DeliveryReport.from_query(
        {"id_state": "598801503", "state": "DELIVRD", "time": "2023-07-23 21:41:20", "error": "0"}
    )
    assert report.id_state == 598801503
    assert report.state is DeliveryState.DELIVERED
    assert report.delivered
    assert report.time == datetime(2023, 7, 23, 21, 41, 20)
    assert report.error is None
    assert report.ack == "598801503"


def test_dlr_hlr_and_unknown_state():
    report = DeliveryReport.from_query(
        {"id_state": "1", "state": "NEWSTATE", "error": "17", "hlr[mcc]": "255", "hlr[mnc]": "01"}
    )
    assert report.state == "NEWSTATE"
    assert report.error == "17"
    assert report.hlr == {"mcc": "255", "mnc": "01"}


def test_dlr_invalid():
    with pytest.raises(ValueError):
        DeliveryReport.from_query({"state": "DELIVRD"})


def test_verify_api_key():
    assert verify_api_key({}, None)
    assert verify_api_key({"Api_Key": "k"}, "k")
    assert verify_api_key({"API-KEY": "k"}, "k")
    assert not verify_api_key({"API_KEY": "x"}, "k")
    assert not verify_api_key({}, "k")
