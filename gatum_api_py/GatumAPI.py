import requests
import urllib.parse


class GatumAPI:

    def __init__(self, base_url, token):
        self.__token = token

        # GET API URLs
        # Send SMS path:
        self.__send_sms_path = base_url + '/send?'

        # Headers:
        self.__headers = {
            'accept': '* / *'
        }

    def send_sms(self, phone, sender_id, text, sms_type=None, lifetime=None, begin_date=None, begin_time=None,
                 delivery=None):
        params = {'token': self.__token, 'phone': phone, 'senderID': sender_id, 'text': text}

        if sms_type is not None:
            params.update({'type': sms_type})
        if lifetime is not None:
            params.update({'lifetime': lifetime})
        if begin_date is not None:
            params.update({'beginDate': begin_date})
        if begin_time is not None:
            params.update({'beginTime': begin_time})
        if delivery is not None:
            params.update({'delivery': delivery})

        response = self._make_request(path=self.__send_sms_path, params=params)
        return response

    def _make_request(self, path, params):
        full_url = path + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        response = requests.get(full_url, headers=self.__headers)
        response.raise_for_status()
        return response
