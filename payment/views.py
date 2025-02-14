from django.shortcuts import render, redirect
from cart.cart import Cart
from payment.forms import ShippingForm, PaymentForm
from payment.models import ShippingAddress, Order, OrderItem
from django.contrib.auth.models import User
from django.contrib import messages
from nails4you.models import Product, Profile
import datetime
#import paypal
from django.urls import reverse
from paypal.standard.forms import PayPalPaymentsForm
from django.conf import settings
import uuid

def orders(request, pk):
	if request.user.is_authenticated and request.user.is_superuser:
		order = Order.objects.get(id=pk)
		items = OrderItem.objects.filter(order=pk)

		if request.POST:
			status = request.POST['shipping_status']
			if status == "true":
				order = Order.objects.filter(id=pk)
				now = datetime.datetime.now()
				order.update(shipped=True, date_shipped=now)
			else:
				order = Order.objects.filter(id=pk)
				order.update(shipped=False)
			messages.success(request, "Versandstatus aktualisiert")
			return redirect('index')


		return render(request, 'payment/orders.html', {"order":order, "items":items})




	else:
		messages.success(request, "Zugriff verweigert")
		return redirect('index')


def not_shipped_dash(request):
	if request.user.is_authenticated and request.user.is_superuser:
		orders = Order.objects.filter(shipped=False)
		if request.POST:
			status = request.POST['shipping_status']
			num = request.POST['num']
			order = Order.objects.filter(id=num)
			now = datetime.datetime.now()
			order.update(shipped=True, date_shipped=now)
			messages.success(request, "Versandstatus aktualisiert")
			return redirect('index')

		return render(request, "payment/not_shipped_dash.html", {"orders":orders})
	else:
		messages.success(request, "Zugang verweigert")
		return redirect('index')
	
	
def shipped_dash(request):
	if request.user.is_authenticated and request.user.is_superuser:
		orders = Order.objects.filter(shipped=True)
		if request.POST:
			status = request.POST['shipping_status']
			num = request.POST['num']
			order = Order.objects.filter(id=num)
			now = datetime.datetime.now()
			order.update(shipped=False)
			messages.success(request, "Versandstatus aktualisiert")
			return redirect('index')


		return render(request, "payment/shipped_dash.html", {"orders":orders})
	else:
		messages.success(request, "Zugriff verweigert")
		return redirect('index')
	

def process_order(request):
	if request.POST:
		cart = Cart(request)
		cart_products = cart.get_prods
		quantities = cart.get_quants
		totals = cart.cart_total()

		# Rechnungsinformationen von der letzten Seite abrufen
		payment_form = PaymentForm(request.POST or None)
		# Daten der Versandsitzung abrufen
		my_shipping = request.session.get('my_shipping')

		# Auftragsinformationen sammeln
		full_name = my_shipping['shipping_full_name']
		email = my_shipping['shipping_email']
		# Versandadresse aus Sitzungsinformationen erstellen
		shipping_address = f"{my_shipping['shipping_address1']}\n{my_shipping['shipping_address2']}\n{my_shipping['shipping_city']}\n{my_shipping['shipping_state']}\n{my_shipping['shipping_zipcode']}\n{my_shipping['shipping_country']}"
		amount_paid = totals

		# Einen Auftrag erstellen
		if request.user.is_authenticated:
			user = request.user
			create_order = Order(user=user, full_name=full_name, email=email, shipping_address=shipping_address, amount_paid=amount_paid)
			create_order.save()

			
			order_id = create_order.pk
			
			for product in cart_products():
				product_id = product.id
				if product.is_sale:
					price = product.sale_price
				else:
					price = product.price

				for key,value in quantities().items():
					if int(key) == product.id:
						create_order_item = OrderItem(order_id=order_id, product_id=product_id, user=user, quantity=value, price=price)
						create_order_item.save()

			# Warenkorb löschen
			for key in list(request.session.keys()):
				if key == "session_key":
					del request.session[key]

			# Warenkorb aus der Datenbank löschen (old_cart field)
			current_user = Profile.objects.filter(user__id=request.user.id)
			# Einkaufswagen in der Datenbank löschen (old_cart field)
			current_user.update(old_cart="")


			messages.success(request, "Bestellung aufgegeben!")
			return redirect('index')

			

		else:
			# Nicht eingeloggt
			# Auftrag erstellen
			create_order = Order(full_name=full_name, email=email, shipping_address=shipping_address, amount_paid=amount_paid)
			create_order.save()

			
			order_id = create_order.pk
			
			for product in cart_products():
				product_id = product.id
				if product.is_sale:
					price = product.sale_price
				else:
					price = product.price

				for key,value in quantities().items():
					if int(key) == product.id:
						create_order_item = OrderItem(order_id=order_id, product_id=product_id, quantity=value, price=price)
						create_order_item.save()

			for key in list(request.session.keys()):
				if key == "session_key":
					del request.session[key]



			messages.success(request, "Bestellung aufgegeben!")
			return redirect('index')


	else:
		messages.success(request, "Zugriff verweigert")
		return redirect('index')

def billing_info(request):
	if request.POST:
		cart = Cart(request)
		cart_products = cart.get_prods
		quantities = cart.get_quants
		totals = cart.cart_total()

		my_shipping = request.POST
		request.session['my_shipping'] = my_shipping

		full_name = my_shipping['shipping_full_name']
		email = my_shipping['shipping_email']

		# Versandadresse aus Sitzungsinformationen erstellen
		shipping_address = f"{my_shipping['shipping_address1']}\n{my_shipping['shipping_address2']}\n{my_shipping['shipping_city']}\n{my_shipping['shipping_state']}\n{my_shipping['shipping_zipcode']}\n{my_shipping['shipping_country']}"
		amount_paid = totals

		host = request.get_host()
		# Rechnungsnummer erstellen
		my_Invoice = str(uuid.uuid4())
		
		# Paypal Formular erstellen
		paypal_dict = {
			'business': settings.PAYPAL_RECEIVER_EMAIL,
			'amount': totals,
			'item_name': 'Book Order',
			'no_shipping': '2',
			'invoice': my_Invoice,
			'currency_code': 'EUR', # EUR for Euros
			'notify_url': 'https://{}{}'.format(host, reverse("paypal-ipn")),
			'return_url': 'https://{}{}'.format(host, reverse("payment_success")),
			'cancel_return': 'https://{}{}'.format(host, reverse("payment_failed")),
		}

		# Paypal-Schaltfläche erstellen
		paypal_form = PayPalPaymentsForm(initial=paypal_dict)

		# Prüfen, ob der Benutzer angemeldet ist
		if request.user.is_authenticated:
			# Abrechnungsformular
			billing_form = PaymentForm()

			# eingeloggt
			user = request.user
			# Auftrag erstellen
			create_order = Order(user=user, full_name=full_name, email=email, shipping_address=shipping_address, amount_paid=amount_paid, invoice = my_Invoice)
			create_order.save()

			
			# Abrufen der Auftrags-ID
			order_id = create_order.pk
			
			# Informationen zum Produkt
			for product in cart_products():
				# Produkt ID
				product_id = product.id
				# Produkt Preis
				if product.is_sale:
					price = product.sale_price
				else:
					price = product.price

				# Anzahl
				for key,value in quantities().items():
					if int(key) == product.id:
						# Auftrags Produkt erstellen
						create_order_item = OrderItem(order_id=order_id, product_id=product_id, user=user, quantity=value, price=price)
						create_order_item.save()

			# Warenkorb aus der Datenbank löschen (old_cart field)
			current_user = Profile.objects.filter(user__id=request.user.id)
			# Einkaufswagen in der Datenbank löschen (old_cart field)
			current_user.update(old_cart="")


			return render(request, "payment/billing_info.html", {"paypal_form":paypal_form, "cart_products":cart_products, "quantities":quantities, "totals":totals, "shipping_info":request.POST, "billing_form":billing_form})

		else:
			# nicht eingeloggt
			# auftrag erstellen
			create_order = Order(full_name=full_name, email=email, shipping_address=shipping_address, amount_paid=amount_paid, invoice = my_Invoice)
			create_order.save()


			order_id = create_order.pk
			
			for product in cart_products():
				product_id = product.id
				if product.is_sale:
					price = product.sale_price
				else:
					price = product.price

				for key,value in quantities().items():
					if int(key) == product.id:
						create_order_item = OrderItem(order_id=order_id, product_id=product_id, quantity=value, price=price)
						create_order_item.save()

			# nicht eingeloggt
			billing_form = PaymentForm()
			return render(request, "payment/billing_info.html", {"paypal_form":paypal_form, "cart_products":cart_products, "quantities":quantities, "totals":totals, "shipping_info":request.POST, "billing_form":billing_form})

	else:
		messages.success(request, "Zugriff verweigert")
		return redirect('index')


def checkout(request):
	cart = Cart(request)
	cart_products = cart.get_prods
	quantities = cart.get_quants
	totals = cart.cart_total()

	if request.user.is_authenticated:
		# Checkout als angemeldeter Benutzer
		# Versand Benutzer
		shipping_user = ShippingAddress.objects.get(user__id=request.user.id)
		# Versand Form
		shipping_form = ShippingForm(request.POST or None, instance=shipping_user)
		return render(request, "payment/checkout.html", {"cart_products":cart_products, "quantities":quantities, "totals":totals, "shipping_form":shipping_form })
	else:
		# Als Gast auschecken
		shipping_form = ShippingForm(request.POST or None)
		return render(request, "payment/checkout.html", {"cart_products":cart_products, "quantities":quantities, "totals":totals, "shipping_form":shipping_form})


def payment_success(request):
	#den Browser-Warenkorb löschen
	cart = Cart(request)
	cart_products = cart.get_prods
	quantities = cart.get_quants
	totals = cart.cart_total()

	# warenkorb löschen
	for key in list(request.session.keys()):
		if key == "session_key":
			# key löschen
			del request.session[key]

	return render(request, 'payment/payment_success.html', {})


def payment_failed(request):

    return render(request, 'payment/payment_failed.html', {})
