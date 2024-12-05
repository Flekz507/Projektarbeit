from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver
from django.conf import settings
import time
from .models import Order

@receiver(valid_ipn_received)
def paypal_payment_received(sender, **kwargs):
    #add a ten second pause for paypal to send ipn data
    time.sleep(10)
    #grab the info that paypal sends
    paypal_obj = sender
    #grab the invoice
    my_Invoice = str(paypal_obj.invoice)

    #match the paypal invoice to the order invoice
    #look up the order
    my_Order = Order.objects.get(invoice=my_Invoice)

    #record the order was paid
    my_Order.paid = True
    #save the order
    my_Order.save()

    #print(paypal_obj)
    #print(f'Amout Paid: {paypal_obj.mc_gross}')