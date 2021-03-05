from django.urls import path
from . import views

urlpatterns = [
    path('searchTeacher/', views.search_teacher),
    path('searchCourses/', views.search_courses),
    path('getGeneralCourseInfo/', views.get_general_course_info),
    path('getMyCourseInfo/', views.get_my_course_info),
    path('createClasses/', views.create_classes),
    path('getSchedule/', views.get_schedule),
    path('removeChangeGroupRequest/', views.remove_change_group_request),
    path('createChangeGroupRequest/', views.create_change_group_request),
    path('getChangeGroupRequestInfo/', views.get_change_group_request_info),
]
