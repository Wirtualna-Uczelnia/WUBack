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
from datetime import datetime, timedelta
from django.utils import timezone
from hashlib import sha512

from jwt import decode, InvalidTokenError, encode


logger = logging.getLogger('mylogger')
JWT_SECRET = "asfiwenbuijfngskejngskdjnksjdn"


@csrf_exempt
def find_matching_names(request, pattern):
    response = HttpResponse()
    token = request.COOKIES['access_token']
    if not can_i_do_stuff_the_role_can_do_having_such_token(token, "student"):
        response.status_code = 401
        return response
    matches = set(WU_User.objects.filter(first_name__iregex=r"^{}".format(pattern))) | set(
        WU_User.objects.filter(last_name__iregex=r"^{}".format(pattern)))
    matches = [(user.username, user.first_name, user.last_name)
               for user in list(matches)]
    response.content = str(matches[0:5])
    return response


@csrf_exempt
def add_member(request):
    if not can_i_do_stuff_the_role_or_above_can_do_having_such_token(token, "teacher"):
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())
    # requests.post(body)


@csrf_exempt
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

    if role == 'teacher':
        if type_of_member == "Student":
            return False
        elif type_of_member == "Teacher":
            return True
    elif role == 'student':
        return True

    return False
