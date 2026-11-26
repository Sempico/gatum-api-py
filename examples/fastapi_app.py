"""Run: SEMPICO_API_TOKEN=... uvicorn examples.fastapi_app:app --port 8000"""

from fastapi import Depends, FastAPI

from sempico_api import AsyncSempicoClient, DeliveryReport
from sempico_api.contrib.fastapi import SempicoLifespan, create_dlr_router, get_client


async def on_dlr(report: DeliveryReport) -> None:
    print(f"DLR: {report.id_state} -> {report.state} at {report.time}")


app = FastAPI(lifespan=SempicoLifespan())
app.include_router(create_dlr_router(on_dlr, path="/sempico/dlr"))


@app.post("/sms")
async def send(phone: str, text: str, client: AsyncSempicoClient = Depends(get_client)):
    result = await client.send_sms(phone, "Info", text)
    return {"id_state": result.id_state, "parts": result.parts}
