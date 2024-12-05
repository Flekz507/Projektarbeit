from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('preview/',views.preview, name='preview'),
    path('shop/', views.shop, name='shop'),
    path('about/', views.about, name='about'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('update_password/', views.update_password, name='update_password'),
    path('update_user/', views.update_user, name='update_user'),
    path('update_info/', views.update_info, name='update_info'),
    path('product/<int:pk>', views.product, name='product'),
    path('category/<str:foo>', views.category, name='category'),
    path('category_summary/', views.category_summary, name='category_summary'),
    path('search/', views.search, name='search'),
    path('book_appointment/', views.book_appointment, name='book_appointment'),
    path('user_appointment/', views.user_appointment, name='user_appointment'),
    path('admin_appointments/', views.admin_appointments, name='admin_appointments'),
    path('admin_appointments/<int:appointment_id>/', views.admin_appointments, name='admin_appointments'),
]