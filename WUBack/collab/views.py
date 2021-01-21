from django.http import HttpResponse, response
from usersauth.models import WU_User
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from django import forms
import logging
import json
import requests
from datetime import datetime, timedelta
from django.utils import timezone
from hashlib import sha512

from jwt import decode, InvalidTokenError, encode




logger = logging.getLogger("mylogger")
JWT_SECRET = "asfiwenbuijfngskejngskdjnksjdn"


@csrf_exempt
def get_matching_names(request):
    response = HttpResponse()
    body = json.loads(request.body.decode())
    patterns = body["pattern"].split()

    token = request.COOKIES["access_token"]
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
    pass


@ csrf_exempt
def add_team(request):
    response = HttpResponse()
    token = request.COOKIES["access_token"]

    if not can_i_do_stuff_the_role_or_above_can_do_having_such_token(token, "teacher"):
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())
    access_token, instance_url = getSfInfo()
    create_team_data = {
        "records" :[
            {
                "attributes" : {
                    "type" : "Team__c"
                },
                "Subject__c": "Temat 1", # body['subject']
                "Description__c": "Opis 1" # body['description']
            },
            ]
        }

    teams_id_list = requests.post(
        instance_url+"/services/data/v48.0/composite/sobjects/", data=create_team_data,headers={"Authorization": "Bearer "+access_token}).json()
    user_id = body['user_id']

    if teams_id_list[0]['success']:
        create_team_member_data = {
            "records" :[
                {
                    "attributes" : {
                        "type" : "Team_Member__c"
                    },
                    "Didactic_Group_Member__r": {
                    "Login__c": "Kimkolwiek" # user_id
                    },
                    "Team__r": {
                        "Id" : teams_id_list[0]['id']
                    }    
                },
            ]
        }

        team_member_list = requests.post(
            instance_url+"/services/data/v48.0/composite/sobjects/", data=create_team_member_data, headers={"Authorization": "Bearer "+access_token}).json()
        if not team_member_list[0]['success']:
            response.status_code = 404
            response.content = "Error with adding team member"
            return response

    response.status_code = 200
    response.content = "Team successfully added"
    return response


@ csrf_exempt
def remove_member(request):
    if not can_i_do_stuff_the_role_or_above_can_do_having_such_token(token, "teacher"):
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())
    # requests.post(body)


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
