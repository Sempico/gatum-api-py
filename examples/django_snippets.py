"""Django wiring, split by file. Copy the parts into your project.

# settings.py
SEMPICO = {"TOKEN": os.environ["SEMPICO_API_TOKEN"], "DLR_API_KEY": os.environ.get("SEMPICO_DLR_API_KEY")}

# urls.py
from django.urls import path
from sempico_api.contrib.django import DeliveryReportView
urlpatterns = [path("sempico/dlr/", DeliveryReportView.as_view())]

# sms/models.py
class Message(models.Model):
    id_state = models.BigIntegerField(unique=True)
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=16, default="ENROUTE")

# sms/receivers.py  (import in SmsConfig.ready())
from django.dispatch import receiver
from sempico_api.contrib.django import dlr_received

@receiver(dlr_received)
def on_dlr(sender, report, **kwargs):
    Message.objects.filter(id_state=report.id_state).update(status=report.state)

# sms/services.py
from sempico_api.contrib.django import get_client

def send_otp(phone: str, code: str) -> Message:
    result = get_client().send_sms(phone, "Verify", f"Your code: {code}")
    return Message.objects.create(id_state=result.id_state, phone=phone)
"""
