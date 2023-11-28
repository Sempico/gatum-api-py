# Python library for Gatum API

The library for interacting with [Gatum GET API](https://api.gatum.io/desc/)

Requires Python 3.10 or later.

## Getting Started

To use the library, first install it from PyPI using `pip`:

    pip install gatum-api-py


## Usage for Gatum GET API
Once you have installed the library, get an API token from Gatum WEB application.
### Send SMS

```py
from gatum_api_py import GatumAPI

# base_url parameter must be set according to your vendor:
client = GatumAPI(base_url='https://api.gatum.io', token='your_token')

# .send_sms() returns a requests library object with server response data
response = client.send_sms(phone='380957225759',  # required, destination phone number in MSISDN format
                           sender_id='Verify',  # required, numeric SID length must be 3-15 symbols, 
                                                # alphanumeric SID length must be <= 11 symbols
                           text='Your OTP is 4542',  # required
                           sms_type='sms',  # optional, allowed types: 'sms', 'hlr', 'mnp', by default: 'sms'
                           lifetime='86400',  # optional, how many seconds this SMS will live, by default: '86400'
                           begin_date='2023-03-19',  # optional, the date when SMS should be sent,
                                                     # format: 'YYYY-MM-DD', by default: the current date
                           begin_time='19:16:00', # optional, the time when SMS should be sent in GMT+0 in selected beginDate,
                                                  # format: 'HH:MM:SS', by default: the current time
                           delivery=False)  # optional, whether to return the DLR, 'TRUE' or 'FALSE', by default: 'TRUE'

print(response.json())
```
### Receive DLR 
To receive DLR, you need to go to the `API` > `GET` section in your WEB cabinet and in the `DLR sending to webhook` field, specify the webhook URL where Gatum should send them.<br><br>
For example, you specified the URL of your webhook as `https://yourdomain.com/apidlr`, in this case, to send DLR Gatum will make a GET request to the URL `https://yourdomain.com/apidlr?id_state=598801503&state=DELIVRD&time=2023-07-23+21%3A41%3A20` <br>
To confirm that you received the DLR, you need to return the value of the `id_state` parameter in response to this request. <br><br>
An example of a simple listener written using the Python Flask framework:
```py
from flask import Flask, request
from urllib.parse import urlparse, parse_qs, unquote

app = Flask(__name__)


@app.route('/apidlr', methods=['GET'])
def receive_dlr():
    url = request.url
    parsed_url = urlparse(url)
    query_string = unquote(parsed_url.query)
    query_params = parse_qs(query_string) if parsed_url.query else {}

    params = {}
    for key, values in query_params.items():
        params[key] = values[0] if len(values) == 1 else values

    print(params)

    return params['id_state'], 200


if __name__ == "__main__":
    app.run(debug=False, port=3000)

```
The output: 
```
{'id_state': '672887248', 'state': 'DELIVRD', 'time': '2023-11-28 13:23:13'}
```



