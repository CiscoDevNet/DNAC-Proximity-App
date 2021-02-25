from webexteamssdk import WebexTeamsAPI, ApiError
import logging
import json
import time
import requests
from datetime import datetime
import datetime as dt
from requests.auth import HTTPBasicAuth
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# ### BOT AND DNAC INFO - TO COME FROM Hashi VAULT or hardcode below ###
BOT_TOKEN = ''
BOT_ACCOUNT = ''
BOT_ID = ''
DNAC_USER = ''
DNAC_PASS = ''
DNAC_URL = ''
api = WebexTeamsAPI(access_token=BOT_TOKEN)
DNAC_AUTH = HTTPBasicAuth(DNAC_USER, DNAC_PASS)


def handle(event, context):
    logger.info('### EVENT INFO \n {}'.format(json.dumps(event)))
    if 'detail-type' in event:
        logger.info('### KEEP ALIVE FUNCTION')
    elif 'resource' in event:
        attachment_handler(event)
    else:
        generate_report(event)


def attachment_handler(event):
    try:
        form_data = api.attachment_actions.get(event['data']['id'])
        logger.info(form_data)
        post_response(form_data)
    except ApiError as e:
        logger.info(e)


def post_response(form_data):
    response = """ *✅ Your submission has been received and report is being generated based on:*
- **Username**: {}
- **Report Timeframe**: {} Days
- **Exposure Time**: {} Minutes
- **Additional Notes** {}

*Please Hold!*
    """.format(form_data.inputs['username'], form_data.inputs['report_days'],
               form_data.inputs['exposure_time'], form_data.inputs['notes'])
    try:
        msg = api.messages.create(roomId=form_data.roomId, markdown=response)
    except ApiError as e:
        logger.info(e)
    # Call DNA Center Proximity API and Pass data entered from user:
    client_proximity(form_data.inputs['username'], form_data.inputs['report_days'], form_data.inputs['exposure_time'])


def get_dnac_jwt_token(dnac_auth):
    """
    Create the authorization token required to access DNA C
    Call to Cisco DNA Center - /api/system/v1/auth/login
    :param dnac_auth - Cisco DNA Center Basic Auth string
    :return: Cisco DNA Center JWT token
    """
    url = DNAC_URL + '/dna/system/api/v1/auth/token'
    header = {'content-type': 'application/json'}
    response = requests.post(url, auth=dnac_auth, headers=header, verify=False)
    dnac_jwt_token = response.json()['Token']
    return dnac_jwt_token


def client_proximity(client_username, days, resolution):
    """
    This function will start the task to collect the client proximity info for the {client_username}
    for {days} in the past, and a time resolution {resolution}. The data that will be generated will be sent to the
    webhook destination subscribed to the event id {NETWORK-CLIENTS-3-506}.
    Proximity is defined as presence on the same floor and building, at the same time with the specified client
    :param client_username: client username
    :param days: how many days in the past maximum 14
    :param resolution: minimum time that will be reported for proximity, recommended 15 min, minimum 5 minutes
    :return: execution id information
    """
    url = DNAC_URL + '/dna/intent/api/v1/client-proximity'
    url += '?username=' + client_username
    url += '&number_days=' + str(days)
    url += '&time_resolution=' + str(resolution)
    header = {'content-type': 'application/json', 'x-auth-token': get_dnac_jwt_token(DNAC_AUTH)}
    response = requests.get(url, headers=header, verify=False)
    response_json = response.json()
    return response_json


def exposure_time(start_time_ep, end_time_ep):
    date_fmt = '%Y-%m-%d %H:%M:%S'
    start_stamp = ''
    end_stamp = ''
    exp_time_ep = {'start': int(start_time_ep), 'end': int(end_time_ep)}
    for key, time_ep in exp_time_ep.items():
        s, ms = divmod(time_ep, 1000)
        timestamp = time.strftime(date_fmt, time.localtime(s))
        if key == 'start':
            start_stamp = datetime.strptime(timestamp, date_fmt)
        else:
            end_stamp = datetime.strptime(timestamp, date_fmt)
    td = end_stamp - start_stamp
    time_diff = int(round(td.total_seconds()))
    return str(dt.timedelta(seconds=time_diff))


def generate_report(tracing_data):
    """
    This function will parse Proximity Data received from DNA Center Webhook.
    See /lambda/proximity-report for complete report generation or simply export the data out to text below
    """
    for client_proximity in tracing_data.json()['details']['client_proximity']:
        for client_info in client_proximity['client_info']:
            for client in client_info['users_info']:
                if 'client_user' in client:
                    print(client['client_user'], client['client_mac'], client['client_type'],
                                      exposure_time(client_info['start_time'], client_info['end_time']),
                                      client_info['location'])

