from django.urls import path
from . import views

urlpatterns = [
    path('searchTeacher/', views.search_teacher),
    path('getSchedule/', views.get_schedule),
    path('createClasses/', views.create_classes),
]
