from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_user),
    path('change/', views.change_pass),
    path('valid/<code>/', views.validate),
    path('login/', views.login),
]
