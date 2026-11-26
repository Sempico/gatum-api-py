from __future__ import annotations

import importlib
import sys
from urllib.parse import parse_qs, urlsplit

import pytest

requests = pytest.importorskip("requests")


@pytest.fixture
def legacy(monkeypatch):
    pytest.importorskip("gatum_api_py")
    sys.modules.pop("gatum_api_py", None)
    sys.modules.pop("gatum_api_py.GatumAPI", None)
    with pytest.warns(FutureWarning, match="sempico-api"):
        module = importlib.import_module("gatum_api_py")
    return module


def test_send_sms_is_1x_compatible(legacy, monkeypatch):
    seen = {}

    def fake_get(url, headers, timeout):
        seen.update(url=url, headers=headers, timeout=timeout)
        resp = requests.Response()
        resp.status_code = 200
        resp._content = b'{"380501234567": 42}'
        return resp

    monkeypatch.setattr(requests, "get", fake_get)
    client = legacy.GatumAPI(base_url="https://api.example.test/", token="secret")
    response = client.send_sms(
        phone="380501234567", sender_id="Verify", text="Code 4542 & more",
        sms_type="sms", lifetime="86400", begin_date="2026-01-01", begin_time="10:00:00",
        delivery=False,
    )

    assert isinstance(response, requests.Response)
    assert response.json() == {"380501234567": 42}
    parts = urlsplit(seen["url"])
    assert parts.path == "/send"
    q = {k: v[0] for k, v in parse_qs(parts.query).items()}
    assert q == {
        "token": "secret", "phone": "380501234567", "senderID": "Verify",
        "text": "Code 4542 & more", "type": "sms", "lifetime": "86400",
        "beginDate": "2026-01-01", "beginTime": "10:00:00", "delivery": "FALSE",
    }
    assert seen["timeout"] == 30
    assert "secret" not in repr(client)


def test_http_error_still_raised(legacy, monkeypatch):
    def fake_get(url, headers, timeout):
        resp = requests.Response()
        resp.status_code = 401
        resp._content = b'{"error": "Incorrect token"}'
        return resp

    monkeypatch.setattr(requests, "get", fake_get)
    with pytest.raises(requests.HTTPError):
        legacy.GatumAPI("https://api.example.test", "bad").send_sms("1", "SMS", "x")
