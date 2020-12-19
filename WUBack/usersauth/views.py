from django.http import HttpResponse
from usersauth.models import WU_User
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from django import forms
import logging
import json
import requests
from jwt import encode
from datetime import datetime, timedelta
from django.utils import timezone
from hashlib import sha512


logger = logging.getLogger('mylogger')
JWT_SECRET = "asfiwenbuijfngskejngskdjnksjdn"


@csrf_exempt
def login(request):
    body = json.loads(request.body.decode())
    username = body['username']
    password = body['password']
    user = authenticate(request, username=username, password=password)
    response = HttpResponse()

    if user is not None:
        access_token, instance_url = getSfInfo()
        sf_user_info = requests.get(
            instance_url+f"/services/data/v50.0/sobjects/Didactic_Group_Member__c/Login__c/{username}", headers={"Authorization": "Bearer "+access_token}).json()
        returned_fields = ['First_Name__c', "Lastname__c", "Type_of_Member__c"]

        response_content = {key: sf_user_info[key]
                            for key in sf_user_info if key in returned_fields}

        response.content = json.dumps(response_content)
        response.status_code = 200
        jwt_token = encode({
            "username": username
        }, JWT_SECRET, "HS256")
        response.set_cookie("access_token", value=jwt_token,
                            secure=True, httponly=True, max_age=120000, samesite='None')
        response.set_cookie('kasia', 'basia', samesite="None",
                            secure=True)

    else:
        response.content = 'Invalid login credentials'
        response.status_code = 401
    return response


@csrf_exempt
def create_user(request):
    batch = json.loads(request.body.decode())['users']
    created = 0

    for user in batch:
        username = user['username']
        code = user['code']

        init_pass = sha512((username + code).encode()).hexdigest()
        expiration_date = datetime.now().date() + timedelta(days=5)

        try:
            u = WU_User.objects.create_user(
                username=username, password=init_pass, code=code
            )
        except IntegrityError:
            logger.error(f'user \'{username}\' already exists')
        else:
            u.code_expiration_date = expiration_date
            u.save()
            created += 1

    return HttpResponse(f'{created} of {len(batch)} users created\n', status=200)


@csrf_exempt
def change_pass(request):
    body = json.loads(request.body.decode())
    code = body['code']
    new_password = body['new_password']

    if not code or not new_password:
        return HttpResponse('Cannot have neither empty code nor empty password\n', status=400)

    user = (WU_User.objects.filter(code=code))[0]
    if not user:
        return HttpResponse('No user with such code\n', status=401)

    if is_expired(user.code_expiration_date):
        return HttpResponse('Cannot change password\n', status=400)

    user.set_password(new_password)
    user.code, user.code_expiration_date = ('', None)

    user.save()
    return HttpResponse(f'Password changed to: {new_password}\n', status=200)


@csrf_exempt
def validate(request, code):
    user = WU_User.objects.filter(code=code)
    if not user:
        return HttpResponse('No user with such code\n', status=401)

    user = list(user)[0]
    expiration = user.code_expiration_date

    if not is_expired(expiration):
        return HttpResponse('Yayx, you can change this guy!\n', status=200)

    return HttpResponse('Too late, sorry mate\n', status=401)


@csrf_exempt
def del_user(request):
    try:
        body = json.loads(request.body.decode())
        username = body['username']
        user = (WU_User.objects.filter(username=username))[0]
        user.delete()
    except Exception as _:
        return HttpResponse('User does not exist!\n', status=500)

    return HttpResponse('User deleted\n', status=200)


def is_expired(date):
    today = timezone.now()
    return today > date


def getSfInfo():
    params_dict = {'grant_type': 'password',
                   'client_id': '3MVG9SOw8KERNN09H9Ywj70jHzsxSfITp8bSXOp69yPjy4ZSWvhPi9pChcztDAo5UT8gSe9nHdHQcPlvLADp6',
                   'client_secret': '386DEF04C4F6D5DE1217D6AD231C585AF802EA4ED331CB91BA8C5C5A8530806E',
                   'username': 'integrationuser@kk-demo.com',
                   'password': 'Integracja1iK03DXGbZpON8LbIpSqA474W'}

    resp = requests.post(
        'https://login.salesforce.com/services/oauth2/token', params=params_dict)

    return resp.json()['access_token'], resp.json()['instance_url']
