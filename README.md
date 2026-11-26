<p align="center">
  <a href="https://sempico.solutions">
    <img src="https://sempico.solutions/wp-content/uploads/2025/09/Logo.png" alt="Sempico Solutions" height="72">
  </a>
</p>

<h1 align="center">Sempico Solutions SMS API for Python</h1>

<p align="center">
  The official Python client for the <a href="https://api.sempico.solutions/desc/">Sempico Solutions SMS API</a>:
  send SMS, run HLR and MNP lookups, and receive delivery reports (DLR).
</p>

<p align="center">
  <a href="https://pypi.org/project/sempico-api/"><img alt="PyPI" src="https://img.shields.io/pypi/v/sempico-api.svg"></a>
  <a href="https://pypi.org/project/sempico-api/"><img alt="Python" src="https://img.shields.io/pypi/pyversions/sempico-api.svg"></a>
  <a href="https://github.com/Sempico/gatum-api-py/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Sempico/gatum-api-py/actions/workflows/ci.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
</p>

---

## Features

- **Sync and async clients** (`SempicoClient`, `AsyncSempicoClient`) built on [`httpx`](https://www.python-httpx.org/)
- **Typed results** (`SendResult`, `DeliveryReport`) instead of raw HTTP responses, with a `py.typed` marker
- **Exceptions per error type**: `BadRequestError` (`no_money`, `incorrect_phone`, ...), `AuthenticationError`, `PermissionDeniedError`
- **Webhook helpers** that parse DLRs and check the `API_KEY` header in any framework
- **Ready-made integrations** for **Django**, **FastAPI** and **Flask**
- **Safe defaults**: HTTPS only, timeouts, retries on connection errors only (an SMS is never sent twice), and the token never shows up in `repr()`

## Installation

```bash
pip install sempico-api
```

With framework integrations:

```bash
pip install "sempico-api[django]"   # or [fastapi], [flask]
```

Requires Python 3.10+.

## Quick start

Create an API token in the Sempico Solutions Web app (**API → GET**).

```python
from sempico_api import SempicoClient

with SempicoClient(token="YOUR_TOKEN") as client:
    result = client.send_sms(
        phone="380501234567",  # international format, digits only
        sender_id="Verify",    # numeric: 3–15 digits, alphanumeric: up to 11 chars
        text="Your code: 4542",
    )

print(result.id_state)   # 1855153903, store it to match the delivery report
print(result.parts)      # number of SMS parts
```

If you don't pass `token=` and `base_url=`, the client reads the `SEMPICO_API_TOKEN` and `SEMPICO_BASE_URL` environment variables:

```bash
export SEMPICO_API_TOKEN="YOUR_TOKEN"
```

> **White-label partners:** pass your own host, e.g. `SempicoClient(base_url="https://api.your-brand.com")`.

### All `send_sms` options

```python
from datetime import datetime, timedelta, timezone
from sempico_api import MessageType

client.send_sms(
    phone="380501234567",
    sender_id="Verify",
    text="Your code: 4542",
    type=MessageType.SMS,               # SMS (default), FLASHSMS, WAPPUSH, VCARD, HLR, MNP
    lifetime=timedelta(hours=1),        # how long to retry delivery; default 86400 s
    send_at=datetime(2026, 12, 1, 9, 0, tzinfo=timezone.utc),  # scheduled send; converted to UTC
    callback_url="https://example.com/sempico/dlr",            # DLR webhook for this message
    delivery=True,                      # send DLRs (default True)
)
```

### Async

```python
import asyncio
from sempico_api import AsyncSempicoClient

async def main() -> None:
    async with AsyncSempicoClient() as client:
        results = await asyncio.gather(
            *(client.send_sms(p, "Promo", "Black Friday −30%") for p in ["380501234567", "380671234567"])
        )
        print([r.id_state for r in results])

asyncio.run(main())
```

### HLR / MNP lookups and replacement preview

```python
client.hlr_lookup("380501234567")   # the result arrives in the DLR, in report.hlr
client.mnp_lookup("380501234567")

preview = client.check_replacement("380501234567", "Verify", "Your code: 4542")
print(preview.sender, preview.content, preview.parts, preview.mcc, preview.mnc)
```

`check_replacement` shows how the routing rules would change the sender and text. It does not send anything.

## Error handling

```python
from sempico_api import (
    AuthenticationError, BadRequestError, ErrorCode,
    PermissionDeniedError, SempicoConnectionError,
)

try:
    client.send_sms("380501234567", "Verify", "Your code: 4542")
except BadRequestError as e:
    if e.error == ErrorCode.NO_MONEY:
        notify_billing()
    else:
        log.warning("SMS rejected: %s", e.error)  # incorrect_phone, blocked_originator, ...
except AuthenticationError:
    ...  # 401: wrong token
except PermissionDeniedError:
    ...  # 403: IP is not in the whitelist, or API is disabled for the account
except SempicoConnectionError:
    ...  # network problem; safe to retry later
```

| Exception | HTTP | Typical `error` values |
|---|---|---|
| `BadRequestError` | 400 | `incorrect_phone`, `incorrect_phone_length`, `no_mcc_mnc`, `phone_in_black_list`, `no_active_aggregator`, `no_source_price`, `no_client_price`, `no_money`, `blocked_originator`, `blocked_shortener_rule`, `undefined_code`, `Rejected by daily limit` |
| `AuthenticationError` | 401 | `Incorrect token` |
| `PermissionDeniedError` | 403 | `IP is not in WhiteList`, `You are not allowed to send via API`, `API is not available` |
| `SempicoConnectionError` | — | DNS, TLS, timeout, connection reset |

All of them inherit from `SempicoError`.

## Delivery reports (DLR)

Sempico Solutions sends the status of every SMS part as a **GET** request to the message's `callback_url`, or to the webhook URL set in the Web app (**API → GET → DLR sending to webhook**):

```
GET https://example.com/sempico/dlr?id_state=598801503&state=DELIVRD&time=2023-07-23+21%3A41%3A20
```

| Parameter | Description |
|---|---|
| `id_state` | ID returned by `send_sms` (one per part) |
| `state` | `DELIVRD`, `UNDELIV`, `EXPIRED`, `ENROUTE` |
| `time` | Status time |
| `error` | Error code, only if it is not `0` |
| `hlr[...]` | HLR data, only for HLR requests |

If a security key is set for the account, it is sent in the `API_KEY` header. Your endpoint must return **HTTP 200**. When confirmation mode is on, the body must be the `id_state`. The integrations below always return it, so they work in both modes.

> **Behind nginx?** nginx drops headers that contain an underscore, such as `API_KEY`, unless you set `underscores_in_headers on;`. Recent gunicorn versions drop them too. If the header never arrives, check the proxy first.

Framework-agnostic parsing:

```python
from sempico_api import DeliveryReport, DeliveryState, verify_api_key

if not verify_api_key(request_headers, expected="YOUR_SECURITY_KEY"):
    ...  # reject with 403
report = DeliveryReport.from_query(query_params)   # any Mapping
report.id_state, report.state, report.time, report.error, report.hlr
report.state is DeliveryState.DELIVERED            # or report.delivered
return report.ack                                   # "598801503"
```

## Framework integrations

### Django

```python
# settings.py
SEMPICO = {
    "TOKEN": os.environ["SEMPICO_API_TOKEN"],
    "DLR_API_KEY": os.environ.get("SEMPICO_DLR_API_KEY"),  # optional
    # "BASE_URL": "https://api.sempico.solutions",          # optional
}
```

```python
# urls.py
from django.urls import path
from sempico_api.contrib.django import DeliveryReportView

urlpatterns = [
    path("sempico/dlr/", DeliveryReportView.as_view(), name="sempico-dlr"),
]
```

```python
# sms/receivers.py  (import it in AppConfig.ready())
from django.dispatch import receiver
from sempico_api.contrib.django import dlr_received

@receiver(dlr_received)
def on_dlr(sender, report, **kwargs):
    Message.objects.filter(id_state=report.id_state).update(status=report.state)
```

```python
# anywhere: views, Celery tasks, management commands
from sempico_api.contrib.django import get_client

result = get_client().send_sms(user.phone, "Verify", f"Your code: {code}")
Message.objects.create(id_state=result.id_state, phone=user.phone)
```

`DeliveryReportView` is CSRF-exempt, accepts only GET, checks `API_KEY` and answers with `id_state`.

### FastAPI

```python
from fastapi import Depends, FastAPI
from sempico_api import AsyncSempicoClient, DeliveryReport
from sempico_api.contrib.fastapi import SempicoLifespan, create_dlr_router, get_client

async def on_dlr(report: DeliveryReport) -> None:
    await db.messages.update(report.id_state, status=report.state)

app = FastAPI(lifespan=SempicoLifespan())   # one shared AsyncSempicoClient
app.include_router(create_dlr_router(on_dlr, path="/sempico/dlr", api_key="YOUR_SECURITY_KEY"))

@app.post("/otp")
async def send_otp(phone: str, client: AsyncSempicoClient = Depends(get_client)):
    result = await client.send_sms(phone, "Verify", "Your code: 4542")
    return {"id_state": result.id_state}
```

### Flask

```python
from flask import Flask
from sempico_api import DeliveryReport
from sempico_api.contrib.flask import Sempico

app = Flask(__name__)
app.config["SEMPICO_API_TOKEN"] = "YOUR_TOKEN"
app.config["SEMPICO_DLR_API_KEY"] = "YOUR_SECURITY_KEY"  # optional
sempico = Sempico(app)

@sempico.dlr_handler("/sempico/dlr")
def on_dlr(report: DeliveryReport) -> None:
    print(f"SMS {report.id_state}: {report.state.value} at {report.time}")

@app.post("/otp")
def send_otp():
    result = sempico.client.send_sms("380501234567", "Verify", "Your code: 4542")
    return {"id_state": result.id_state}
```

Runnable versions are in [`examples/`](examples/).

## Migrating from `gatum-api-py` 1.x

The `gatum-api-py` package and the `GatumAPI` class are now **`sempico-api`** and **`SempicoClient`**.

`gatum-api-py` **1.1.0** is a compatibility release. It keeps 1.0.x code working unchanged, shows a `FutureWarning` about the rename, and installs `sempico-api` as a dependency. Its source is in [`legacy/gatum-api-py`](legacy/gatum-api-py/).

| 1.x | 2.x |
|---|---|
| `pip install gatum-api-py` | `pip install sempico-api` |
| `from gatum_api_py import GatumAPI` | `from sempico_api import SempicoClient` |
| `GatumAPI(base_url=..., token=...)` | `SempicoClient(token=..., base_url=...)` (`base_url` is optional) |
| `send_sms(..., sms_type="sms")` | `send_sms(..., type=MessageType.SMS)` |
| `begin_date=..., begin_time=...` | `send_at=datetime(...)` |
| returns `requests.Response` → `.json()` | returns `SendResult` → `.id_state` |
| `requests.HTTPError` | `BadRequestError` / `AuthenticationError` / ... |

## Development

```bash
pip install -e ".[dev,django,fastapi,flask]"
pytest
ruff check . && mypy
```

## Support

- API reference: <https://api.sempico.solutions/desc/>
- Website: <https://sempico.solutions>
- Email: <support@sempico.solutions>

---

<p align="center">© Sempico Solutions Group LTD · MIT License</p>
