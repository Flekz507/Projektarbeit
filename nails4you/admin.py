from django.contrib import admin
from .models import Product
from .models import Category
from .models import Profile
from .models import Appointment
from django.contrib.auth.models import User
# Register your models here.

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Profile)
admin.site.register(Appointment)

#mix profile info and user info
class ProfileInline(admin.StackedInline):
    model = Profile

#exted user model
class UserAdmin(admin.ModelAdmin):
    model = User
    field = ["username", "first_name", "last_name", "email"]
    inlines = [ProfileInline]

#unregister old way
admin.site.unregister(User)

#register the new way
admin.site.register(User, UserAdmin)