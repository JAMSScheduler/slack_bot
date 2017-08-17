#!/usr/bin/python
import time
import requests
import json
from slackclient import SlackClient

# Bot ID and various tokens we need
slack_bot_key = ''
bot_id = ''
jams_user = ''
jams_pass = ''
uri_base = 'http://JAMS_API_URI/JAMS'
auth_uri = uri_base + '/api/authentication/login'
jobs_uri = uri_base + '/api/entry'
get_submit_uri = uri_base + '/api/submit?name='
find_job_uri = uri_base + '/api/job/'
post_submit_uri = uri_base + '/api/submit'
get_vars_uri = uri_base + '/api/variable?name='
put_vars_uri = uri_base + '/api/variable/'
creds = {'username': jams_user, 'password': jams_pass}

# Slackbot commands/call
at_bot = '<@' + bot_id + '>'
run_command = 'run job'
find_command = 'find job'
help_command = 'help'
failed_command = 'get failed jobs'
update_var = 'update variable'

# Job and variable blacklist -
# any jobs here cannot be run by the bot
# any variables cannot be updated by the bot
job_blacklist = ['SampleBlackListJob', 'AnotherBlacklistedJob']
var_blacklist = []


# Instantiate the Slack client
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


def find_jams_job(job_name, token):
    """
        Finds a JAMS Job and will return the parent folder. If there are
        duplicate Jobs it will return all of them, storing in a list.
    """
    jobs = requests.get(find_job_uri,
                        headers={'Authorization': 'Bearer ' + token,
                                 'content-type': 'application/json'})
    if jobs.status_code == 200:
        jobs = jobs.json()
        found_jobs = []
        for i in range(len(jobs)):
            if jobs[i]['jobName'].lower() == job_name:
                found_jobs.append(jobs[i]['parentFolderName'])
        return found_jobs
    else:
        return "*ERROR!* Status code {} was returned.".format(jobs.status_code)


def run_jams_job(job_name, token):
    """
        Takes in the name of the job and a token to submit a specific JAMS
        Job that's not found in the Blacklist.
    """
    # Is the job found in our blacklist?
    if job_name not in [x.lower() for x in job_blacklist]:
        # We need to pass our token to JAMS for authorization
        job_info = requests.get(get_submit_uri + job_name,
                                headers={'Authorization': 'Bearer ' + token,
                                         'content-type': 'application/json'})
        job_info = job_info.json()
        r = requests.post(post_submit_uri,
                          data=json.dumps(job_info),
                          headers={'Authorization': 'Bearer ' + token,
                                   'content-type': 'application/json'})
        if r.status_code == 200:
            response = '*{}* was successfully submitted to run!' \
                        .format(job_name)
        elif r.status_code == 422:
            response = '*{}* was not found in JAMS. Typo?'.format(job_name)
        else:
            response = '*ERROR!* Response code was: {}'.format(r.status_code)
    else:
        response = '*ERROR!* {} is in the blacklist!'.format(job_name)
    return response


def update_jams_var_value(var_name, new_value, token):
    """
        Takes in the name of a variable, an updated value, and a token to
        update the value of a JAMS Variable var_blacklist.
    """
    # Is the job found in our blacklist?
    if var_name not in [x.lower() for x in var_blacklist]:
        # We need to pass our token to JAMS for authorization
        var_info = requests.get(get_vars_uri + var_name,
                                headers={'Authorization': 'Bearer ' + token,
                                         'content-type': 'application/json'})
        var_info = var_info.json()
        var_info['value'] = new_value
        r = requests.put(put_vars_uri,
                         data=json.dumps(var_info),
                         headers={'Authorization': 'Bearer ' + token,
                                  'content-type': 'application/json'})
        if r.status_code == 200:
            response = '*{}* was successfully updated!' \
                        .format(var_name)
        elif r.status_code == 422:
            response = '*{}* was not found in JAMS. Typo?'.format(var_name)
        else:
            response = '*ERROR!* Response code was: {}'.format(r.status_code)
    else:
        response = '*ERROR!* {} is in the blacklist!'.format(var_name)
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
    response = 'Not sure what you mean. My available commands are: \n \
                *{}*, *{}*, *{}*, *{}*, and *{}*'.format(run_command,
                                                         failed_command,
                                                         find_command,
                                                         help_command,
                                                         update_var)
    if command.startswith(help_command):
        response = 'Available commands: \
                       \n\t - *help* \
                       \n\t - *run job [job name]* \
                       \n\t - *find job [job name]* \
                       \n\t - *update variable [name] [value]* \
                       \n\t - *get failed jobs*'
    if command.startswith(find_command):
        job_name = command.split('find job ')[1]
        token = get_jams_token(jams_user, jams_pass)
        job_location = find_jams_job(job_name, token)
        if len(job_location) == 1:
            response = '*{}* found in {}'.format(job_name, job_location[0])
        elif len(job_location) > 1:
            response = '*' + job_name + \
                       '* found in multiple locations: \n\t-' + \
                       '\n\t-'.join(job_location)
        else:
            response = '*ERROR!* Job {} not found! Typo?'.format(job_name)
    if command.startswith(update_var):
        split_values = command.split('update variable ')[1]
        values = split_values.split(' value ')
        var_name = values[0]
        updated_var_value = values[1]
        token = get_jams_token(jams_user, jams_pass)
        response = update_jams_var_value(var_name, updated_var_value, token)
    if command.startswith(failed_command):
        token = get_jams_token(jams_user, jams_pass)
        failed_list = get_failed_jobs(token)
        if len(failed_list) > 0:
            response = 'Failed Jobs: \n\t-' + '\n\t-'.join(failed_list)
        else:
            response = 'No failed Jobs to report on!'
    if command.startswith(run_command):
        job_name = command.split('run job ')[1]
        token = get_jams_token(jams_user, jams_pass)
        response = run_jams_job(job_name, token)
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
