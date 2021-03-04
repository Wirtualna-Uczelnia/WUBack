from django.urls import path
from . import views

urlpatterns = [
    path('searchTeacher/', views.search_teacher),
    path('searchCourses/', views.search_courses),
    path('createClasses/', views.create_classes),
    path('getSchedule/', views.get_schedule),
]
