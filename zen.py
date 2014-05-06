# Import the required libraries.
# ---------------------------------------------------------------------------------------------------------------------#
import requests
import csv
from django.utils.encoding import smart_str
import time
import os
import datetime
import calendar
import sys

# ---------------------------------------------------------------------------------------------------------------------#
# ZenDesk class to handle authentication and methods to access the API
# ---------------------------------------------------------------------------------------------------------------------#
class ZenDesk:
    # to get and hold authentication information
    def __init__(self, zendesk_url, zendesk_username, zendesk_token):
        self.zendesk_url = zendesk_url
        self.zendesk_username = zendesk_username
        self.zendesk_token = zendesk_token

    # function to access the Incremental Ticket API and return the response
    def incremental_ticket_pull(self, start_time):
        headers = {'Accept': 'application/json'}
        zendesk_endpoint = '/exports/tickets.json?start_time='
        url = self.zendesk_url + zendesk_endpoint + str(start_time)
        response = requests.get(url, auth=(self.zendesk_username, self.zendesk_token), headers=headers)
        return response
    
    # function to access the Ticket Comments API and return the response
    def ticket_comment_pull(self, ticket_id):
        headers = {'Accept': 'application/json'}
        zendesk_endpoint = '/tickets/' + str(ticket_id) + '/comments.json'
        url = self.zendesk_url + zendesk_endpoint
        response = requests.get(url, auth=(self.zendesk_username, self.zendesk_token), headers=headers)
        return response

    # function to handle the responses ZenDesk sends
    def status_handler(self, response):
        if response.status_code==429:
            print('Rate limited. Waiting to retry in ' + response.headers.get('retry-after') + ' seconds.')
            time.sleep(float(response.headers.get('retry-after')))
        if 200 <= response.status_code <= 300:
            print('Success.')
        if response.status_code==422:
            print("Start time is too recent. Try a start_time older than 5 minutes.")
            sys.exit(0)

    # function to return the epoch time for a certain number of days and/or hours ago
    # useful for routinely pulling tickets at a certain time from the incremental API
    def delta_start_time(self, daysago, hoursago=0):
        return calendar.timegm((datetime.datetime.fromtimestamp(time.time()) -
                                datetime.timedelta(days=daysago, hours=hoursago)).timetuple())

    # function to get the last time from the log, which is the "next_
    def last_log_time(logfile, self):
        return int(file(logfile, "r").readlines()[-1][0:-1])
