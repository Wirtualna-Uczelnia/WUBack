from django.http import HttpResponse, response
from usersauth.models import WU_User
from django.views.decorators.csrf import csrf_exempt

from django import forms
from django.utils import timezone
import logging
import json
import requests
import random
import os

from jwt import decode, InvalidTokenError
from datetime import datetime
from pyzoom import ZoomClient

client = ZoomClient.from_environment()

logger = logging.getLogger("mylogger")
JWT_SECRET = os.getenv('JWT_SECRET')


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


def is_between_dates(event, start_date, end_date):
    event_start_date = datetime.fromisoformat(event.get("Start_Date__c")[:-5])
    event_end_date = datetime.fromisoformat(event.get("End_Date__c")[:-5])
    start_date = datetime.fromisoformat(start_date)
    end_date = datetime.fromisoformat(end_date)

    if event_end_date < start_date or event_start_date > end_date:
        return False

    return True


def is_expired(date):
    today = timezone.now()
    return today > date


def getSfInfo():
    params_dict = {'grant_type': 'password',
                   'client_id': os.getenv('SF_CLIENT_ID'),
                   'client_secret': os.getenv('SF_CLIENT_SECRET'),
                   'username': os.getenv('SF_USERNAME'),
                   'password': os.getenv('SF_PASSWORD')}

    resp = requests.post(
        'https://login.salesforce.com/services/oauth2/token', params=params_dict)

    return resp.json()['access_token'], resp.json()['instance_url']
