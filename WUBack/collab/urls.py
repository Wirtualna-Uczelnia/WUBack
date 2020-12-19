from django.urls import path
from . import views

urlpatterns = [
    path('findMatchingNames/<pattern>/', views.find_matching_names),
    path('addMember/', views.add_member),
    path('removeMember/', views.remove_member),
]
