from django.http import HttpResponse
from usersauth.models import WU_User
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError

from django import forms
import logging
import json
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
        response.content = f'User {username} has logged in'
        response.status_code = 200
        jwt_token = encode({
            "username": username
        }, JWT_SECRET, "HS256")
        response.set_cookie("access_token", value=jwt_token,
                            secure=True, httponly=True, max_age=120, samesite='Lax')
        response.set_cookie('kasia', 'basia')
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Allow-Origin'] = 'https://wirtualna-uczelnia-7534a.web.app/'

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


def is_expired(date):
    today = timezone.now()
    return today > date
