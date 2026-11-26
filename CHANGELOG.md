# Changelog

## 2.0.0 (2026-11-26)

The package is renamed from `gatum-api-py` to **`sempico-api`**. Branding is now **Sempico Solutions**.

### Added
- `SempicoClient` and `AsyncSempicoClient`, built on `httpx`.
- Typed results: `SendResult`, `ReplacementResult`, `DeliveryReport`; enums `MessageType`, `DeliveryState`, `ErrorCode`.
- Exceptions per error type: `BadRequestError`, `AuthenticationError`, `PermissionDeniedError`, `SempicoConnectionError`.
- New `/send` parameters: `callback_url` and `shortener`. All message types: `FLASHSMS`, `WAPPUSH`, `VCARD`, `HLR`, `MNP`.
- `check_replacement()` for the `/replacement` endpoint, and the `hlr_lookup()` / `mnp_lookup()` helpers.
- DLR helpers `DeliveryReport.from_query()` and `verify_api_key()`.
- Integrations: `sempico_api.contrib.django`, `.fastapi`, `.flask`.
- Configuration from `SEMPICO_API_TOKEN` / `SEMPICO_BASE_URL`; the default host is `https://api.sempico.solutions`.
- `py.typed`, a test suite, and CI.

### Changed
- `send_at: datetime` replaces `begin_date` and `begin_time`, with automatic UTC conversion.
- `delivery` is now sent as `TRUE`/`FALSE`. 1.x sent `True`/`False`.
- Requests have a 30 s timeout (1.x could hang forever) and retry on connection errors only.
- Only HTTPS is allowed, because the token is part of the URL.
- Packaging moved to `pyproject.toml` (hatchling).

### Removed
- `setup.py` and `requirements.txt`. The old `requirements.txt` was UTF-16 encoded and pip could not read it.
- The `requests` dependency.

### Deprecated
- `gatum_api_py` is no longer part of `sempico-api`. It ships only in `gatum-api-py` 1.1.0, so the two packages never write the same files.

## gatum-api-py 1.1.0 (2026-11-26)

A compatibility release of the old package. Source: `legacy/gatum-api-py`.

- `GatumAPI` keeps the 1.0.x signature, returns a `requests.Response` and raises `requests.HTTPError`.
- A `FutureWarning` about the rename to `sempico-api` is shown on import.
- `sempico-api>=2,<3` is now a dependency.
- Fixed: requests have a 30 s timeout, `delivery=True/False` is sent as `TRUE`/`FALSE`, and the `Accept` header is valid.
- Fixed: the token no longer appears in `repr()`.
