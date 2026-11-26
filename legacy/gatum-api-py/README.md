<p align="center">
  <a href="https://sempico.solutions">
    <img src="https://sempico.solutions/wp-content/uploads/2025/09/Logo.png" alt="Sempico Solutions" height="72">
  </a>
</p>

# gatum-api-py is now `sempico-api`

> **This package is deprecated and will not get new features.**
> Please switch to [**`sempico-api`**](https://pypi.org/project/sempico-api/), the official Python client for the
> [Sempico Solutions SMS API](https://api.sempico.solutions/desc/).

Version 1.1.0 is a compatibility release:

- Your 1.0.x code keeps working unchanged. `GatumAPI.send_sms()` still returns a `requests.Response` and still raises `requests.HTTPError`.
- Importing `gatum_api_py` shows a `FutureWarning` that tells you about the rename.
- `sempico-api` is installed as a dependency, so you can switch imports right away.
- Bug fixes: requests now have a 30-second timeout (1.0.x could hang forever), `delivery=True/False` is sent as `TRUE`/`FALSE`, and the `Accept` header is now valid.

## Migrate in two steps

```bash
pip uninstall gatum-api-py
pip install sempico-api
```

```python
# before
from gatum_api_py import GatumAPI
client = GatumAPI(base_url="https://api.sempico.solutions", token="YOUR_TOKEN")
response = client.send_sms(phone="380501234567", sender_id="Verify", text="Your code: 4542")
print(response.json())

# after
from sempico_api import SempicoClient
client = SempicoClient(token="YOUR_TOKEN")
result = client.send_sms(phone="380501234567", sender_id="Verify", text="Your code: 4542")
print(result.id_state)
```

The full migration guide, the async client, and the Django, FastAPI and Flask integrations are documented at
<https://github.com/Sempico/gatum-api-py#migrating-from-gatum-api-py-1x>.

---

© Sempico Solutions Group LTD · MIT License · <support@sempico.solutions>
