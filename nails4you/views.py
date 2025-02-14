from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .forms import SignUpForm, UpdateUserForm, ChangePasswordForm, UserInfoForm
from payment.forms import ShippingForm
from payment.models import ShippingAddress
from django import forms
from .models import *
from cart.cart import Cart
import json
from .forms import AppointmentForm
from .models import Appointment

def search(request):
	# Formular ausgefüllt?
	if request.method == "POST":
		searched = request.POST['searched']
		# Abfrage des DB-Modells Produkte
		searched = Product.objects.filter(Q(name__icontains=searched) | Q(description__icontains=searched))
		if not searched:
			messages.success(request, "Diese Produkt schein nicht zu existieren...versuche es nochmal.")
			return render(request, "search.html", {})
		else:
			return render(request, "search.html", {'searched':searched})
	else:
		return render(request, "search.html", {})

def update_info(request):
	if request.user.is_authenticated:
		# Aktuellen Benutzer abrufen
		current_user = Profile.objects.get(user__id=request.user.id)
		# Versandinformationen des aktuellen Benutzers abrufen
		shipping_user = ShippingAddress.objects.get(user__id=request.user.id)
		
		# Original-Benutzerformular abrufen
		form = UserInfoForm(request.POST or None, instance=current_user)
		# Versandformular des Benutzers abrufen
		shipping_form = ShippingForm(request.POST or None, instance=shipping_user)		
		if form.is_valid() or shipping_form.is_valid():
			# Originalformular speichern
			form.save()
			# Versandformular speichern
			shipping_form.save()

			messages.success(request, "Deine Informationen wurden geändert!!")
			return redirect('index')
		return render(request, "update_info.html", {'form':form, 'shipping_form':shipping_form})
	else:
		messages.success(request, "Du muss eingeloggt sein um diese Seite zu betreten!!")
		return redirect('index')

def update_password(request):
	if request.user.is_authenticated:
		current_user = request.user
		if request.method  == 'POST':
			form = ChangePasswordForm(current_user, request.POST)
			if form.is_valid():
				form.save()
				messages.success(request, "Password geändert...")
				login(request, current_user)
				return redirect('update_user')
			else:
				for error in list(form.errors.values()):
					messages.error(request, error)
					return redirect('update_password')
		else:
			form = ChangePasswordForm(current_user)
			return render(request, "update_password.html", {'form':form})
	else:
		messages.success(request, "Du muss eingeloggt sein um diese Seite sehen zu können...")
		return redirect('index')


def update_user(request):
    if request.user.is_authenticated:
        current_user = User.objects.get(id=request.user.id)
        user_form = UpdateUserForm(request.POST or None, instance=current_user)

        if user_form.is_valid():
            user_form.save()

            login(request, current_user)
            messages.success(request, "Bentzer Info wurde geändert")
            return redirect('index')
        
        return render(request, 'update_user.html', {'user_form':user_form})
    
    else:

        messages.success(request, "You must be logged in to access that page")
        return redirect('index')

def category_summary(request):
    categories = Category.objects.all()
    return render(request, 'category_summary.html', {'categories':categories})

def category(request, foo):
    foo = foo.replace('-', ' ')
    try:
        category = Category.objects.get(name=foo)
        products = Product.objects.filter(category=category)
        return render(request, 'category.html', {'products':products, 'category':category})

    except:
        messages.success(request,("Diese Kategorie existiert nicht..."))
        return redirect('shop')


def product(request, pk):
    product = Product.objects.get(id=pk)
    return render(request, 'product.html', {'product':product})

def base(request):
    return render(request, 'base.html')

def index(request):
    return render(request, 'index.html')

def preview(request):
    return render(request, 'preview.html')

def shop(request):
    products = Product.objects.all()
    return render(request, 'shop.html', {'products':products})

def about(request):
    return render(request, 'about.html')

def login_user(request):
	if request.method == "POST":
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(request, username=username, password=password)
		if user is not None:
			login(request, user)

			current_user = Profile.objects.get(user__id=request.user.id)
			saved_cart = current_user.old_cart
			if saved_cart:
				converted_cart = json.loads(saved_cart)

				cart = Cart(request)
				for key,value in converted_cart.items():
					cart.db_add(product=key, quantity=value)

			messages.success(request, ("Du wurdest eingeloggt!"))
			return redirect('index')
		else:
			messages.success(request, ("Es gab einen Fehler, bitte versuche es nochmal..."))
			return redirect('login')

	else:
		return render(request, 'login.html', {})

def logout_user(request):
    logout(request)
    messages.success(request,("Du wurdest ausgeloggt..."))
    return redirect('index')

def register_user(request):
    form = SignUpForm()
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            #login user
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request,("Benutzername wurde erstellt - bitte fülle deine Benutzerinformationen in der Nachfolgende Seite aus"))
            return redirect('update_info')
        else:
            messages.success(request,("Es gab einen Fehler bei der Registrierung, bitte versuche es nochmal..."))
            return redirect('register')
    else:
        return render(request, 'register.html', {'form':form})
    
def book_appointment(request):
    # Überprüfen, ob der Benutzer eingeloggt ist
    if not request.user.is_authenticated:
        messages.success(request, "Du musst eingeloggt sein, um einen Termin zu buchen.")
        return redirect('index')  # Weiterleitung zur Startseite

    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.user = request.user  # Benutzer dem Termin zuweisen
            appointment.save()  # Termin speichern
            messages.success(request, "Ihr Termin wurde erfolgreich gebucht!")
            return redirect('index')  # Weiterleitung zur Startseite (oder Bestätigungsseite)

    else:
        form = AppointmentForm()

    return render(request, 'book_appointment.html', {'form': form})

def user_appointment(request):
    if request.user.is_authenticated:
        appointments = Appointment.objects.filter(user=request.user)
        
        if request.method == 'POST':
            # Prüfen, ob der Benutzer einen Termin löschen möchte
            if "delete_appointment_id" in request.POST:
                appointment_id = request.POST.get("delete_appointment_id")
                appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
                appointment.delete()
                messages.success(request, "Termin wurde erfolgreich gelöscht!")
                return redirect('user_appointment')
            
            # Ansonsten: Bearbeitung des Termins
            appointment_id = request.POST.get("appointment_id")
            appointment = get_object_or_404(Appointment, id=appointment_id, user=request.user)
            form = AppointmentForm(request.POST, instance=appointment)
            if form.is_valid():
                form.save()
                messages.success(request, "Termin wurde erfolgreich aktualisiert!")
                return redirect('user_appointment')
        else:
            form = AppointmentForm()

        return render(request, 'user_appointment.html', {'appointments': appointments,'form': form,})
    else:
        messages.error(request, "Du musst eingeloggt sein, um deine Termine zu sehen.")
        return redirect('index')
    

def admin_appointments(request, appointment_id=None):
    if request.user.is_authenticated and request.user.is_superuser:
        # Wenn ein Termin bearbeitet wird
        if appointment_id:
            appointment = get_object_or_404(Appointment, id=appointment_id)
            if request.method == 'POST':
                form = AppointmentForm(request.POST, instance=appointment)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Termin wurde erfolgreich aktualisiert!")
                    return redirect('admin_appointments')  # Zurück zur Übersicht nach der Bearbeitung
            else:
                form = AppointmentForm(instance=appointment)
            return render(request, 'admin_appointments.html', {
                'form': form,
                'appointment_to_edit': appointment,  # Zeigt an, dass wir im Bearbeitungsmodus sind
            })
        
        # Übersicht aller Termine
        appointments = Appointment.objects.all().order_by('-date', '-time')
        
        # Prüfen, ob ein Termin gelöscht werden soll
        if request.method == 'POST' and 'delete_appointment_id' in request.POST:
            appointment_id_to_delete = request.POST.get("delete_appointment_id")
            appointment_to_delete = get_object_or_404(Appointment, id=appointment_id_to_delete)
            appointment_to_delete.delete()
            messages.success(request, "Termin wurde erfolgreich gelöscht!")
            return redirect('admin_appointments')

        # Standard: Liste der Termine anzeigen
        return render(request, 'admin_appointments.html', {'appointments': appointments,})

    # Zugriff verweigert, wenn kein Admin
    messages.error(request, "Sie müssen als Admin angemeldet sein, um diese Seite zu sehen.")
    return redirect('index')
