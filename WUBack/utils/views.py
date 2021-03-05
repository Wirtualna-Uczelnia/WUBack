import json

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from usersauth.models import WU_User
from .tools import *


@csrf_exempt
def create_change_group_request(request):
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

    from_didactic_group_id = body.get('from_dg_id')
    to_didactic_group_id = body.get('to_dg_id')

    if not from_didactic_group_id or not to_didactic_group_id:
        response.content = "Didactic group ids not provided"
        response.status_code = 400
        return response

    token = decode(token, JWT_SECRET)

    sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id+FROM+Didactic_Group_Member__c+WHERE+Login__c='{token.get('username')}'", headers={
        "Authorization": "Bearer "+access_token}).json()

    didactic_group_member = sf_response.get('records')[0].get('Id')

    change_group_request_dict = {
        "records": [{
            "attributes": {
                "type": "Group_Change_Request__c"
            },
            "From_Group__c": from_didactic_group_id,
            "To_Group__c": to_didactic_group_id,
            "Who__c": didactic_group_member,
        }
        ]
    }

    sf_response = requests.post(instance_url + f"/services/data/v48.0/composite/sobjects/",
                                json=change_group_request_dict, headers={"Authorization": "Bearer "+access_token}).json()

    if not sf_response[0].get('id'):
        response.status_code = 400
        response.content = "Wrong data, change group request not created"
        return response

    response.status_code = 200
    response.content = json.dumps({'id': sf_response[0].get('id')})
    return response


@csrf_exempt
def get_change_group_request_info(request):
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

    from_didactic_group_id = body.get('didactic_group_id')

    if not from_didactic_group_id:
        response.content = "Didactic group id not provided"
        response.status_code = 400
        return response

    sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Course__c,Type_of_classes__c+FROM+Didactic_Group__c+WHERE+Id='{from_didactic_group_id}'", headers={
        "Authorization": "Bearer "+access_token}).json()

    course_id, type_of_classes = sf_response.get('records')[0].get(
        'Course__c'), sf_response.get('records')[0].get('Type_of_classes__c')

    sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id+FROM+Didactic_Group__c+WHERE+Course__c='{course_id}'+AND+Type_of_classes__c='{type_of_classes}'", headers={
        "Authorization": "Bearer "+access_token}).json()

    response.content = f"{sf_response}"
    response.status_code = 200
    return response


@csrf_exempt
def remove_change_group_request(request):
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

    change_group_request_ids = body.get('change_group_request_ids')

    change_group_request_ids = ",".join(
        change_group_request_ids).replace("'", "")

    requests.delete(instance_url + f"/services/data/v49.0/composite/sobjects?ids={change_group_request_ids}&allOrNone=false", headers={
        "Authorization": "Bearer "+access_token})

    response.content = "Change group request(s) successfully removed"
    response.status_code = 200
    return response


@ csrf_exempt
def get_my_course_info(request):
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

    token = decode(token, JWT_SECRET)
    type_of_member = token["member_type"]

    body = json.loads(request.body.decode())

    didactic_group_id = body.get('didactic_group_id')

    if type_of_member == "Teacher":
        course_attendee_list = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Didactic_Group_Member_Login__c+FROM+Didactic_Group_Attendee__c+WHERE+Didactic_Group__c='{didactic_group_id}'", headers={
            "Authorization": "Bearer "+access_token}).json()

        course_info = {attendee.get('Id'): {"login": attendee.get(
            'Didactic_Group_Member_Login__c'), "grades": []} for attendee in course_attendee_list.get('records')}

        attendee_ids = "'" + "','".join(course_info.keys()) + "'"

        grades = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Grade_Value__c,Name,Didactic_Group_Attendee__c+FROM+Grade__c+WHERE+Didactic_Group_Attendee__c+IN+({attendee_ids})", headers={
            "Authorization": "Bearer "+access_token}).json()

        for grade in grades.get('records'):
            course_info[grade.get('Didactic_Group_Attendee__c')]['grades'].append({"id": grade.get(
                'Id'), "name": grade.get('Name'), "value": grade.get('Grade_Value__c')})

        response.content = json.dumps(course_info)
        response.status_code = 200
        return response
    elif type_of_member == "Student":
        sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Didactic_Group_Member_Login__c+FROM+Didactic_Group_Attendee__c+WHERE+Didactic_Group__c='{didactic_group_id}'+AND+Didactic_Group_Member_Login__c='{token.get('username')}'", headers={
            "Authorization": "Bearer "+access_token}).json()

        records = sf_response.get('records')

        if not records:
            response.content = "User is not an attendee of this course"
            response.status_code = 404
            return response

        attendee_id = records[0].get('Id')

        grades = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Grade_Value__c,Name+FROM+Grade__c+WHERE+Didactic_Group_Attendee__c='{attendee_id}'", headers={
            "Authorization": "Bearer "+access_token}).json()

        course_info = {attendee_id: {"login": token.get('username'), "grades": [{"id": grade.get(
            'Id'), "name": grade.get('Name'), "value": grade.get('Grade_Value__c')} for grade in grades.get('records')]}}

        response.content = json.dumps(course_info)
        response.status_code = 200
        return response

    response.status_code = 418
    return response


@ csrf_exempt
def get_general_course_info(request):
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

    course_id = body.get("course_id")

    if not course_id:
        response.content = "Course id not provided"
        response.status_code = 400
        return response

    sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Assessment_methods__c,ECTS__c,Faculty__c,Literature__c,Statute__c,Subject__c+FROM+Course__c+WHERE+Id='{course_id}'", headers={
        "Authorization": "Bearer "+access_token}).json()

    courses_info = [{key: course[key] for key in course if key != 'attributes'}
                    for course in sf_response.get('records')]

    response.content = json.dumps(courses_info[0])
    response.status_code = 200
    return response


@ csrf_exempt
def search_courses(request):
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

    pattern = body.get('pattern')

    sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Faculty__c,Subject__c+FROM+Course__c", headers={
        "Authorization": "Bearer "+access_token}).json()

    courses_list = [{key: course[key] for key in course if key != 'attributes'}
                    for course in sf_response.get('records') if pattern.lower() in course.get('Subject__c').lower()]

    response.content = json.dumps({"records": courses_list})
    response.status_code = 200
    return response


@csrf_exempt
def create_classes(request):
    response = HttpResponse()

    access_token, instance_url = getSfInfo()

    if not access_token:
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())

    classes_id = body.get('id')
    start_date = datetime.fromisoformat(body.get('start_date'))
    end_date = datetime.fromisoformat(body.get('end_date'))
    subject = body.get('subject')

    if not (classes_id and start_date and end_date and subject):
        response.content = "Wrong data"
        response.status_code = 400
        return response

    duration = int((end_date-start_date).total_seconds()/60)
    meeting_pass = str(random.randint(0, 999999)).zfill(6)

    meeting = client.meetings.create_meeting(
        subject, start_time=body.get('start_date'), duration_min=duration, password=meeting_pass)

    meeting_dict = dict(meeting)

    event_dict = {
        "allOrNone": False,
        "records": [{
            "attributes": {
                "type": "Event__c"
            },
            "id": classes_id,
            "Meeting_Link__c": meeting_dict.get("start_url"),
            "Meeting_Id__c": meeting_dict.get("id"),
            "Meeting_Password__c": meeting_pass
        }
        ]
    }

    requests.patch(instance_url + f"/services/data/v48.0/composite/sobjects/",
                   json=event_dict, headers={"Authorization": "Bearer "+access_token})

    response.status_code = 200
    response.content = "Classes successfully created"
    return response


@csrf_exempt
def get_schedule(request):
    response = HttpResponse(content_type='application/json')
    token = request.COOKIES.get("access_token")

    if not token:
        response.content = "No access token cookie"
        response.status_code = 401
        return response

    access_token, instance_url = check_access(token, "student")

    if not access_token:
        response.status_code = 401
        return response

    username = decode(token, JWT_SECRET).get("username")

    sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Meeting__c+FROM+Didactic_Group__c+WHERE+Id+IN+ \
        (SELECT+Didactic_Group__c+FROM+Didactic_Group_Attendee__c+WHERE+Didactic_Group_Member_Login__c='{username}')", headers={
        "Authorization": "Bearer "+access_token}).json()

    events_ids = "'" + \
        "','".join([m.get('Meeting__c')
                    for m in sf_response['records']]) + "'"

    sf_response = requests.get(instance_url + f"/services/data/v50.0/query/?q=SELECT+Id,Subject__c,Description__c,Start_Date__c, \
        End_Date__c,Repeat_Frequency__c,Is_Repetitive__c,Meeting_Link__c+FROM+Event__c+WHERE+Id+IN+({events_ids})", headers={
        "Authorization": "Bearer "+access_token}).json()

    events_list = [{key: event[key] for key in event if key != 'attributes'}
                   for event in sf_response.get('records')]

    response.status_code = 200
    response.content = json.dumps({"records": events_list})
    return response


@csrf_exempt
def search_teacher(request):
    response = HttpResponse()
    token = request.COOKIES.get("access_token")

    if not token:
        response.content = "No access token cookie"
        response.status_code = 401
        return response

    body = json.loads(request.body.decode())
    pattern = body.get("pattern")

    patterns = pattern.split()

    if not can_i_do_stuff_the_role_or_above_can_do_having_such_token(token, "student"):
        response.status_code = 401
        return response

    if not patterns:
        matches = list(WU_User.objects.filter(
            is_student=False).filter(is_admin=False))

    else:
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

        matches = list(matches & set(WU_User.objects.filter(is_student=False)))

    data = []

    for i in range(len(matches)):
        person = dict()
        person["username"] = matches[i].username
        person["firstname"] = matches[i].first_name
        person["lastname"] = matches[i].last_name
        data.append(person)

    matches = dict()
    matches["users"] = data

    response.content = json.dumps(matches)
    return response


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
