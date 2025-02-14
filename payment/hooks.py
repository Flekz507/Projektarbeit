from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver
from django.conf import settings
import time
from .models import Order

@receiver(valid_ipn_received)
def paypal_payment_received(sender, **kwargs):
    #Hinzufügen einer zehnsekündigen Pause, damit Paypal ipn-Daten senden kann
    time.sleep(10)
    #die von Paypal gesendeten Informationen abrufen
    paypal_obj = sender
    #Rechnung
    my_Invoice = str(paypal_obj.invoice)

    #die Paypal-Rechnung mit der Bestellrechnung abgleichen
    my_Order = Order.objects.get(invoice=my_Invoice)

    #Aufzeichnung der Bezahlung der Bestellung
    my_Order.paid = True
    #den Auftrag speichern
    my_Order.save()
