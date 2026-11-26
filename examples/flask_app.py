"""Run: SEMPICO_API_TOKEN=... flask --app examples.flask_app run --port 5000"""

import os

from flask import Flask, request

from sempico_api import DeliveryReport
from sempico_api.contrib.flask import Sempico

app = Flask(__name__)
app.config["SEMPICO_API_TOKEN"] = os.environ["SEMPICO_API_TOKEN"]
sempico = Sempico(app)


@sempico.dlr_handler("/sempico/dlr")
def on_dlr(report: DeliveryReport) -> None:
    print(f"DLR: {report.id_state} -> {report.state} at {report.time}")


@app.post("/sms")
def send():
    result = sempico.client.send_sms(request.args["phone"], "Info", request.args["text"])
    return {"id_state": result.id_state, "parts": result.parts}
