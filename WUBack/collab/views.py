import json
import requests
import random

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, response

from usersauth.models import WU_User
from utils.tools import *
from datetime import datetime


@csrf_exempt
def get_attachments(request):
    response = HttpResponse(content_type="application/json")
    token = request.COOKIES.get("access_token")

    if not token:
        response.content = "No access token cookie"
        response.status_code = 401
        return response

    access_token, instance_url = check_access(token, "student")

    if not access_token:
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())

    parent_id = body.get('parent_id')

    sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Name+FROM+Attachment+WHERE+parentId='{parent_id}'", headers={
        "Authorization": "Bearer "+access_token}).json()

    attachments_list = [{key: attachment[key] for key in attachment if key != 'attributes'}
                        for attachment in sf_response.get('records')]

    response.content = json.dumps({"records": attachments_list})
    response.status_code = 200
    return response


@csrf_exempt
def get_attachment(request):
    response = HttpResponse(content_type="application/json")
    token = request.COOKIES.get("access_token")

    if not token:
        response.content = "No access token cookie"
        response.status_code = 401
        return response

    access_token, instance_url = check_access(token, "student")

    if not access_token:
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())

    attachment_id = body.get("attachment_id")

    attachment_content = requests.get(instance_url + f'/services/data/v50.0/sobjects/Attachment/{attachment_id}/Body', headers={
        "Authorization": "Bearer "+access_token}).content

    response.content = attachment_content
    response.status_code = 200
    return response


@csrf_exempt
def remove_attachments(request):
    response = HttpResponse()
    token = request.COOKIES.get("access_token")

    if not token:
        response.content = "No access token cookie"
        response.status_code = 401
        return response

    access_token, instance_url = check_access(token, "student")

    if not access_token:
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())

    attachments_ids_list = body.get('attachment_ids')

    if not attachments_ids_list:
        response.content = "No attachment id provided"
        response.status_code = 400
        return response

    attachments_ids = ",".join(attachments_ids_list).replace("'", "")

    requests.delete(instance_url + f"/services/data/v49.0/composite/sobjects?ids={attachments_ids}&allOrNone=false", headers={
        "Authorization": "Bearer "+access_token})

    response.content = "Attachments successfully removed"
    response.status_code = 200
    return response


@csrf_exempt
def add_attachment(request):
    response = HttpResponse()
    token = request.COOKIES.get("access_token")

    if not token:
        response.content = "No access token cookie"
        response.status_code = 401
        return response

    access_token, instance_url = check_access(token, "student")

    if not access_token:
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())

    if any(key not in body for key in ["Name", "Body", "parentId"]):
        response.content = "Name, Body, or parentId not provided"
        response.status_code = 400
        return response

    attachment_data = {
        "records": [{
            "attributes": {
                "type": "Attachment"
            },
            **body
        }]
    }

    sf_response = requests.post(instance_url + f"/services/data/v48.0/composite/sobjects/",
                                json=attachment_data, headers={"Authorization": "Bearer "+access_token}).json()

    response.status_code = 200
    response.content = json.dumps({'id': sf_response[0].get('id')})
    return response


@csrf_exempt
def get_events(request):
    response = HttpResponse()
    token = request.COOKIES.get("access_token")

    if not token:
        response.content = "No access token cookie"
        response.status_code = 401
        return response

    access_token, instance_url = check_access(token, "student")

    if not access_token:
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())

    start_date, end_date = body.get('start_date'), body.get('end_date')
    if not start_date or not end_date:
        response.content = "Event start date or end date not provided"
        response.status_code = 400
        return response

    event_owner = body.get("event_owner")
    sf_response = None
    team_id = body.get("team_id")

    if event_owner == "team":
        sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Subject__c,Description__c,Start_Date__c,End_Date__c,Repeat_Frequency__c,Is_Repetitive__c,Team__c,Meeting_Link__c+FROM+Event__c+WHERE+Team__c='{team_id}'", headers={
            "Authorization": "Bearer "+access_token}).json()

        events_list = [{key: event[key] for key in event if key != 'attributes'}
                       for event in sf_response.get('records') if is_between_dates(event, start_date, end_date)]

    elif event_owner == "user":
        team_members = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Didactic_Group_Member_Login__c,Team__c+FROM+Team_Member__c+WHERE+Team__c='{team_id}'", headers={
            "Authorization": "Bearer "+access_token}).json()

        members_logins = "'" + \
            "','".join([m.get('Didactic_Group_Member_Login__c')
                        for m in team_members['records']]) + "'"

        team_members = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Didactic_Group_Member_Login__c,Team__c+FROM+Team_Member__c+WHERE+Didactic_Group_Member_Login__c+IN+({members_logins})", headers={
            "Authorization": "Bearer "+access_token}).json()

        members = [{'login': member.get('Didactic_Group_Member_Login__c'), 'team': member.get(
            'Team__c')} for member in team_members['records'] if member.get('Team__c') != team_id]

        teams_ids = "'"+"','".join(list(set([m.get('Team__c')
                                             for m in team_members.get('records')]))) + "'"

        sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Subject__c,Description__c,Start_Date__c,End_Date__c,Repeat_Frequency__c,Is_Repetitive__c,Team__c,Meeting_Link__c+FROM+Event__c+WHERE+Team__c+IN+({teams_ids})", headers={
            "Authorization": "Bearer "+access_token}).json()

        members_events_list = [{key: event[key] for key in event if key != 'attributes'}
                               for event in sf_response.get('records') if is_between_dates(event, start_date, end_date)]

        events_list = {}
        for login in set([member.get('login') for member in members]):
            teams_ids = [member.get('team')
                         for member in members if member.get('login') == login]
            events = [event for event in members_events_list if event.get(
                'Team__c') in teams_ids]
            events_list[login] = events

    response.status_code = 200
    response.content = json.dumps({"records": events_list})
    return response


@csrf_exempt
def remove_event(request):
    response = HttpResponse()
    token = request.COOKIES.get("access_token")

    if not token:
        response.content = "No access token cookie"
        response.status_code = 401
        return response

    access_token, instance_url = check_access(token, "teacher")

    if not access_token:
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())
    event_id = body.get('event_id')

    sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Meeting_Id__c+FROM+Event__c+WHERE+Id='{event_id}'", headers={
        "Authorization": "Bearer "+access_token}).json()

    if sf_response.get('records'):
        meeting_id = sf_response.get('records')[0].get('Meeting_Id__c')

        try:
            client.meetings.delete_meeting(meeting_id)
        except:
            response.content = "Event zoom meeting id error; "

        requests.delete(instance_url + f"/services/data/v49.0/composite/sobjects?ids={event_id}", headers={
                        "Authorization": "Bearer "+access_token})

        response.status_code = 200
        response.content += b"Event successfully removed"
        return response

    response.status_code = 404
    response.content = "Event not found"
    return response


@csrf_exempt
def edit_event(request):
    response = HttpResponse()
    token = request.COOKIES.get("access_token")

    if not token:
        response.content = "No access token cookie"
        response.status_code = 401
        return response

    access_token, instance_url = check_access(token, "teacher")

    if not access_token:
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())
    event_info = body.get('event_info')

    if not event_info:
        response.content = "Event info not provided"
        response.status_code = 400
        return response

    event_id = event_info.get("id")

    sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Subject__c,Start_Date__c,End_Date__c,Repeat_Frequency__c,Is_Repetitive__c,Meeting_Password__c,Team__c+FROM+Event__c+WHERE+Id='{event_id}'", headers={
        "Authorization": "Bearer "+access_token}).json()

    records = sf_response.get('records')

    if not records:
        response.content = "No such event id"
        response.status_code = 404
        return response

    event_dict = records[0]
    event_dict.update(event_info)

    start_date = datetime.fromisoformat(event_dict.get("Start_Date__c")[:-5])
    end_date = datetime.fromisoformat(event_dict.get("End_Date__c")[:-5])
    duration = int((end_date-start_date).total_seconds()/60)

    meeting = client.meetings.create_meeting(event_dict.get('Subject__c'), start_time=event_dict.get(
        'Start_Date__c'), duration_min=duration, password=event_dict.get('Meeting_Password__c'))

    meeting_dict = dict(meeting)
    event_dict['Meeting_Link__c'] = meeting_dict.get("start_url")
    event_dict['Meeting_Id__c'] = meeting_dict.get("id")

    event_dict = {
        "allOrNone": False,
        "records": [
            event_dict
        ]
    }

    sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Meeting_Id__c+FROM+Event__c+WHERE+Id='{event_id}'", headers={
        "Authorization": "Bearer "+access_token}).json()

    if sf_response.get('records'):
        meeting_id = sf_response.get('records')[0].get('Meeting_Id__c')
        try:
            client.meetings.delete_meeting(meeting_id)
        except:
            response.content = "Event zoom meeting id error; "

    requests.patch(instance_url + f"/services/data/v48.0/composite/sobjects/",
                   json=event_dict, headers={"Authorization": "Bearer "+access_token})

    response.content = "Event successfully edited"
    response.status_code = 200
    return response


@csrf_exempt
def create_event(request):
    response = HttpResponse()
    token = request.COOKIES.get("access_token")

    if not token:
        response.content = "No access token cookie"
        response.status_code = 401
        return response

    access_token, instance_url = check_access(token, "student")

    if not access_token:
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())
    event_info = body.get('event_info')

    if not event_info:
        response.content = "Event info not provided"
        response.status_code = 400
        return response

    meeting_pass = str(random.randint(0, 999999)).zfill(6)
    start_date = datetime.fromisoformat(event_info.get("Start_Date__c")[:-1])
    end_date = datetime.fromisoformat(event_info.get("End_Date__c")[:-1])
    duration = int((end_date-start_date).total_seconds()/60)
    meeting = client.meetings.create_meeting(event_info.get('Subject__c'), start_time=event_info.get(
        'Start_Date__c')[:-1], duration_min=duration, password=meeting_pass)

    meeting_dict = dict(meeting)

    event_dict = {
        "attributes": {
            "type": "Event__c"
        },
        "Meeting_Link__c": meeting_dict.get("start_url"),
        "Meeting_Password__c": meeting_pass,
        "Meeting_Id__c": meeting_dict.get("id")
    }

    event_dict.update(event_info)
    event_dict = {"records": [event_dict]}

    sf_response = requests.post(instance_url + f"/services/data/v48.0/composite/sobjects/",
                                json=event_dict, headers={"Authorization": "Bearer "+access_token}).json()

    if not sf_response[0].get('id'):
        response.status_code = 400
        response.content = "Wrong data, event not created"
        return response

    response.status_code = 200
    response.content = json.dumps({'id': sf_response[0].get('id')})
    return response


@csrf_exempt
def get_team_info(request):
    response = HttpResponse()
    token = request.COOKIES.get("access_token")

    if not token:
        response.content = "No access token cookie"
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())
    team_id = body.get("id")

    if not team_id:
        response.content = "Team id not provided"
        response.status_code = 400
        return response

    access_token, instance_url = check_access(token, "student")

    if not access_token:
        response.status_code = 401
        return response

    sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Subject__c,Description__c+FROM+Team__c+WHERE+Id='{team_id}'", headers={
        "Authorization": "Bearer "+access_token}).json()

    records = sf_response.get('records')
    if not records:
        response.content = "No team with such id"
        response.status_code = 400
        return response

    team_info = records[0]

    team_members = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Didactic_Group_Member_Login__c+FROM+Team_Member__c+WHERE+Team__c='{team_id}'", headers={
                                "Authorization": "Bearer "+access_token}).json()

    team_members_list = [{"id": team_member.get('Id'), 'login': team_member.get(
        'Didactic_Group_Member_Login__c')} for team_member in team_members.get('records')]

    users = [user_exists[0] for team_member in team_members_list if (
        user_exists := list(WU_User.objects.filter(username=team_member['login']))) != []]

    team_members_list = [
        team_member for team_member in team_members_list if team_member['login'] in [user.username for user in users]]

    team_members_info = [{"first_name": user.first_name,
                          "last_name": user.last_name} for user in users]

    for d, i in zip(team_members_list, team_members_info):
        d.update(i)

    response.content = json.dumps({"id": team_info.get('Id'), "subject": team_info.get(
        'Subject__c'), "description": team_info.get('Description__c'), "team_members": team_members_list})
    response.status_code = 200
    return response


@csrf_exempt
def get_paginated_team_list(request):
    response = HttpResponse()
    token = request.COOKIES.get("access_token")

    if not token:
        response.content = "No access token cookie"
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())
    page_number = body.get("page")

    if not page_number:
        response.content = "No page number provided"
        response.status_code = 400
        return response

    page_number = int(page_number)
    access_token, instance_url = check_access(token, "student")

    if not access_token:
        response.status_code = 401
        return response

    sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Subject__c,Description__c+FROM+Team__c+WHERE+Id+IN+(SELECT+Team__c+FROM+Team_Member__c+WHERE+Didactic_Group_Member_Login__c='{decode(token, JWT_SECRET).get('username')}')+ORDER+BY+Subject__c+ASC", headers={
                               "Authorization": "Bearer "+access_token}).json()

    team_list_size, team_list = sf_response.get(
        'totalSize'), sf_response.get('records')

    team_list = [{key: team[key] for key in team if key != 'attributes'}
                 for team in team_list[(page_number-1)*5:page_number*5]]

    response.content = json.dumps({"size": team_list_size, "teams": team_list})
    response.status_code = 200

    return response


@csrf_exempt
def get_matching_names(request):
    response = HttpResponse()
    token = request.COOKIES.get("access_token")

    if not token:
        response.content = "No access token cookie"
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())
    pattern = body.get("pattern")

    if not pattern:
        response.content = "Pattern not provided"
        response.status_code = 400
        return response

    patterns = pattern.split()

    if not can_i_do_stuff_the_role_or_above_can_do_having_such_token(token, "student"):
        response.status_code = 401
        return response

    if len(patterns) > 1:
        first_1 = set(WU_User.objects.filter(
            first_name__iregex=r"^{}".format(patterns[0])))
        last_1 = set(WU_User.objects.filter(
            last_name__iregex=r"^{}".format(patterns[1])))
        first_2 = set(WU_User.objects.filter(
            first_name__iregex=r"^{}".format(patterns[1])))
        last_2 = set(WU_User.objects.filter(
            last_name__iregex=r"^{}".format(patterns[0])))
        matches = (first_1 & last_1) | (first_2 & last_2)
    else:
        first = set(WU_User.objects.filter(
            first_name__iregex=r"^{}".format(patterns[0])))
        last = set(WU_User.objects.filter(
            last_name__iregex=r"^{}".format(patterns[0])))
        matches = first | last

    matches = list(matches)
    data = []
    for i in range(min(5, len(matches))):
        person = dict()
        person["username"] = matches[i].username
        person["firstname"] = matches[i].first_name
        person["lastname"] = matches[i].last_name
        person["isStudent"] = matches[i].is_student
        data.append(person)

    matches = dict()
    matches["users"] = data

    response.content = json.dumps(matches)
    return response


@ csrf_exempt
def add_member(request):
    response = HttpResponse()
    token = request.COOKIES.get("access_token")

    if not token:
        response.content = "No access token cookie"
        response.status_code = 401
        return response

    access_token, instance_url = check_access(token, "teacher")

    if not access_token:
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())
    team_id = body['team_id']

    members_list = []

    for member in body['team_members']:
        members_list.append(
            {
                "attributes": {
                    "type": "Team_Member__c"
                },
                "Didactic_Group_Member__r": {
                    "Login__c": member
                },
                "Team__c": team_id
            }
        )

    create_team_member_data = {
        "records": members_list
    }

    team_member_list = requests.post(
        instance_url+"/services/data/v48.0/composite/sobjects/", json=create_team_member_data, headers={"Authorization": "Bearer "+access_token}).json()
    if not team_member_list[0].get('id'):
        response.status_code = 404
        response.content = "Error with adding team member"
        return response

    response.status_code = 200
    response.content = "Successfully added member to team"
    return response


@ csrf_exempt
def add_team(request):
    response = HttpResponse()
    token = request.COOKIES.get("access_token")

    if not token:
        response.content = "No access token cookie"
        response.status_code = 401
        return response

    access_token, instance_url = check_access(token, "teacher")

    if not access_token:
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())
    create_team_data = {
        "records": [
            {
                "attributes": {
                    "type": "Team__c"
                },
                "Subject__c": body['subject'],
                "Description__c": body['description']
            }
        ]
    }

    teams_id_list = requests.post(
        instance_url+"/services/data/v48.0/composite/sobjects/", json=create_team_data, headers={"Authorization": "Bearer "+access_token}).json()
    teacher_id = body['teacher_id']

    if teams_id_list[0].get('id'):
        members_list = []
        members_list.append(
            {
                "attributes": {
                    "type": "Team_Member__c"
                },
                "Didactic_Group_Member__r": {
                    "Login__c": teacher_id
                },
                "Team__c": teams_id_list[0].get('id')
            }
        )

        for member in body['team_members']:
            members_list.append(
                {
                    "attributes": {
                        "type": "Team_Member__c"
                    },
                    "Didactic_Group_Member__r": {
                        "Login__c": member
                    },
                    "Team__c": teams_id_list[0].get('id')
                }
            )

        create_team_member_data = {
            "records": members_list
        }

        team_member_list = requests.post(
            instance_url+"/services/data/v48.0/composite/sobjects/", json=create_team_member_data, headers={"Authorization": "Bearer "+access_token}).json()

        if not team_member_list[0].get('id'):
            response.status_code = 404
            response.content = "Error with adding team member"
            return response
    else:
        response.status_code = 404
        response.content = "Error with creating team"
        return response

    response.status_code = 200
    response.content = json.dumps({'team_id': teams_id_list[0].get('id')})
    return response


@ csrf_exempt
def remove_member(request):
    response = HttpResponse()
    token = request.COOKIES.get("access_token")

    if not token:
        response.content = "No access token cookie"
        response.status_code = 401
        return response

    access_token, instance_url = check_access(token, "teacher")

    if not access_token:
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())
    team_members_logins = "'"+"','".join(body['team_members'])+"'"
    sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Team__r.Id+FROM+Team_Member__c+WHERE+Didactic_Group_Member_Login__c+IN+({team_members_logins})+AND+Team__r.Id='{body['team_id']}'", headers={
                               "Authorization": "Bearer "+access_token}).json()

    team_member_ids = str([s.get('Id') for s in sf_response['records']]).replace(
        "'", "").replace(" ", "")[1:-1]

    requests.delete(instance_url + f"/services/data/v49.0/composite/sobjects?ids={team_member_ids}&allOrNone=false", headers={
                    "Authorization": "Bearer "+access_token})

    response.status_code = 200
    response.content = f"Users {team_members_logins} successfully removed from team"
    return response
