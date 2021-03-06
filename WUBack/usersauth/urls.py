from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_user),
    path('change/', views.change_pass),
    path('valid/<code>/', views.validate),
    path('login/', views.login),
    path('delete/', views.del_user),
    path('logout/', views.logout),
    path('generateCode/', views.generate_change_password_code)
]
