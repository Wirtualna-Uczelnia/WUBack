from django.urls import path
from . import views

urlpatterns = [
    path("getMatchingNames/", views.get_matching_names),
    path("addMember/", views.add_member),
    path("removeMember/", views.remove_member),
    path("createTeam/", views.add_team),
    path("getTeams/", views.get_paginated_team_list),
    path("teamInfo/", views.get_team_info),
    path("createEvent/", views.create_event),
    path("editEvent/", views.edit_event),
    path("removeEvent/", views.remove_event),
    path("getEvents/", views.get_events),
    path("addAttachment/", views.add_attachment),
    path("getAttachments/", views.get_attachments),
    path("getAttachment/", views.get_attachment),
    path("removeAttachments/", views.remove_attachments),
]
