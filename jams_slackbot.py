import time
import requests
import json
from slackclient import SlackClient

# Bot ID and various tokens we need
slack_bot_key = ''
bot_id = ''
jams_user = ''
jams_pass = ''
uri_base = 'http://host_or_uri/JAMS'
auth_uri = uri_base + '/api/authentication/login'
jobs_uri = uri_base + '/api/entry'
get_submit_uri = uri_base + '/api/submit?name='
post_submit_uri = uri_base + '/api/submit'

creds = {
    'username': jams_user,
    'password': jams_pass
}

# Slackbot variables
at_bot = '<@' + bot_id + '>'
do_command = 'run job'
help_command = 'help'
failed_command = 'get failed jobs'

# Instatniate the Slack client
slack_client = SlackClient(slack_bot_key)


def get_jams_token(jams_user, jams_pass):
    """
        This takes a username and password to authenticate to the JAMS
        REST API and returns a token.
    """
    r = requests.post(auth_uri,
                      data=json.dumps(creds),
                      headers={'content-type': 'application/json'})
    r.raise_for_status()
    resp = r.json()
    return resp['access_token']


def run_jams_job(job_name, token):
    """
        Takes in the name of the job and a token to submit a specific JAMS
        Job
    """
    # We need to pass our token to JAMS for authorization
    job_info = requests.get(get_submit_uri + job_name, 
                            headers={'Authorization': 'Bearer ' + token, 
                                     'content-type': 'application/json'})
    job_info = job_info.json()
    r = requests.post(post_submit_uri,
                      data=json.dumps(job_info),
                      headers=headers)
    if r.status_code == 200:
        response = '{} was successfully Submitted to run!'.format(job_name)
    else:
        response = 'ERROR! Response code was: {}'.format(r.status_code)
    return response


def get_failed_jobs(token):
    """
        Takes in a token and will return the names of any failed Jobs
    """
    # We need to pass our token to JAMS for authorization
    jobs = requests.get(jobs_uri, headers={'Authorization': 'Bearer ' + token,
                                           'content-type': 'application/json'})
    jobs = jobs.json()
    error_jobs = []
    for i in range(len(jobs)):
        if jobs[i]['finalSeverity'] == 'Error':
            error_jobs.append(jobs[i]['jobName'])
    
    return error_jobs


def handle_command(command, channel):
    """
       	Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        it returns back what is needed for clarification.
    """
    response = 'Not sure what you mean. My available commands are: \
    *{}* and *{}*'.format(do_command, help_command)
    if command.startswith(help_command):
        response = 'Available commands: \
                       \n\t - *help* \
                       \n\t - *run job* \
                       \n\t - *get failed jobs*'
    if command.startswith(failed_command):
        token = get_jams_token(jams_user, jams_pass)
        failed_list = get_failed_jobs(token)
        if len(failed_list) > 0:
            response = 'Failed Jobs: \n\t-' + '\n\t-'.join(failed_list)
        else:
            response = 'No failed Jobs to report on!'
    if command.startswith(do_command):
        job_to_run = command.split('run job ')[1]
        token = get_jams_token(jams_user, jams_pass)
        response = run_jams_job(job_to_run, token)
    slack_client.api_call('chat.postMessage', channel=channel,
                          text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehouse.
        This parsing function returns None unless a message is
        directed at the bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and at_bot in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(at_bot)[1].strip().lower(), \
                    output['channel']
    return None, None


if __name__ == '__main__':
    read_websocket_delay = 1
    if slack_client.rtm_connect():
        print('JAMSBot connected and running!')
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(read_websocket_delay)
    else:
        print('Connection failed. Invalid slack token or bot ID?')
