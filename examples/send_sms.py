"""Send one SMS. Run: SEMPICO_API_TOKEN=... python examples/send_sms.py 380501234567"""

import sys

from sempico_api import BadRequestError, SempicoClient

with SempicoClient() as client:
    try:
        result = client.send_sms(sys.argv[1], "Verify", "Hello from Sempico Solutions!")
    except BadRequestError as e:
        sys.exit(f"Rejected: {e.error}")
    print(f"Sent: id_state={result.id_state}, parts={result.parts}")
