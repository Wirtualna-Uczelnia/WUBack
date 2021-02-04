from django.urls import path
from . import views

urlpatterns = [
    path("getMatchingNames/", views.get_matching_names),
    path("addMember/", views.add_member),
    path("removeMember/", views.remove_member),
    path("createTeam/", views.add_team),
    path("getTeams/", views.get_paginated_team_list),
    path("teamInfo/", views.get_team_info)
]
