from django.http import HttpResponse, response
from usersauth.models import WU_User
from django.views.decorators.csrf import csrf_exempt

from django import forms
import logging
import json
import requests

from jwt import decode, InvalidTokenError


logger = logging.getLogger("mylogger")
JWT_SECRET = "asfiwenbuijfngskejngskdjnksjdn"


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

    team_info = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Subject__c,Description__c+FROM+Team__c+WHERE+Id='{team_id}'", headers={"Authorization": "Bearer "+access_token}).json()
    team_members = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Didactic_Group_Member_Login__c+FROM+Team_Member__c+WHERE+Team__c='{team_id}'", headers={"Authorization": "Bearer "+access_token}).json()

    team_members_dict = [{"id": team_member.get('Id'), 'login': team_member.get('Didactic_Group_Member_Login__c')} for team_member in team_members.get('records')]

    team_members_info = [{"first_name": user.first_name, "last_name": user.last_name} for user in [(WU_User.objects.filter(username=team_member['login']))[0] for team_member in team_members_dict]]

    [team_members_dict[i].update(team_members_info[i]) for i in range(0,len(team_members_dict))]

    response.content = json.dumps({"id": team_info['records'][0].get('Id'), "subject": team_info['records'][0].get('Subject__c'), "description": team_info['records'][0].get('Description__c'), "team_members": team_members_dict})
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

    sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Subject__c,Description__c+FROM+Team__c+WHERE+Id+IN+(SELECT+Team__c+FROM+Team_Member__c+WHERE+Didactic_Group_Member_Login__c='{body['login']}')", headers={"Authorization": "Bearer "+access_token}).json()
    team_list_size, team_list = sf_response.get('totalSize'), sf_response.get('records')

    team_list = [{key: team[key] for key in team if key != 'attributes'} for team in team_list[(page_number-1)*5:page_number*5]]
    
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
    sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Team__r.Id+FROM+Team_Member__c+WHERE+Didactic_Group_Member_Login__c='{body['login']}'+AND+Team__r.Id='{body['team_id']}'", headers={"Authorization": "Bearer "+access_token}).json()
    team_member_id = sf_response['records'][0].get('Id')

    requests.delete(instance_url + f"/services/data/v49.0/composite/sobjects?ids={team_member_id}", headers={"Authorization": "Bearer "+access_token})

    response.status_code = 200
    response.content = f"User {body['login']} successfully removed from team"
    return response

def check_access(token, role):
    if not can_i_do_stuff_the_role_or_above_can_do_having_such_token(token, role):
        return False, False
    return getSfInfo()


def can_i_do_stuff_the_role_or_above_can_do_having_such_token(token, role):
    try:
        token = decode(token, JWT_SECRET)
    except InvalidTokenError as e:
        logger.error(str(e))
        return False

    type_of_member = token["member_type"]

    if role == "teacher":
        if type_of_member == "Student":
            return False
        elif type_of_member == "Teacher":
            return True
    elif role == "student":
        return True

    return False


def getSfInfo():
    params_dict = {'grant_type': 'password',
                   'client_id': '3MVG9SOw8KERNN09H9Ywj70jHzsxSfITp8bSXOp69yPjy4ZSWvhPi9pChcztDAo5UT8gSe9nHdHQcPlvLADp6',
                   'client_secret': '386DEF04C4F6D5DE1217D6AD231C585AF802EA4ED331CB91BA8C5C5A8530806E',
                   'username': 'integrationuser@kk-demo.com',
                   'password': 'Integracja1iK03DXGbZpON8LbIpSqA474W'}

    resp = requests.post(
        'https://login.salesforce.com/services/oauth2/token', params=params_dict)

    return resp.json()['access_token'], resp.json()['instance_url']
