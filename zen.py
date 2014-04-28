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
    def last_log_time(self):
        return int(file("log.txt", "r").readlines()[-1][0:-1])


# ---------------------------------------------------------------------------------------------------------------------#

# Main Code to Download and Dump Incremental Tickets
# ---------------------------------------------------------------------------------------------------------------------#
zd = ZenDesk('https://enter_your_zendesk_url_here/api/v2',
             'enter_your_login_email_here/token',
             'enter your API token here')

# set the start time to the last log item, which is the "next_time" for the last pull that occurred
# if this is the first time you're running this, set it to the first day your ZenDesk started in Unix epoch time,
# and switch it back to zd.last_log_time() afterwards
# you can also use the delta_start_time function defined above if you're interestd in tickets from a certain time ago
start_time = zd.last_log_time()

# alternatively you can specify a time manually, or a time a certain number of days and/or hours ago:
# start_time = zd.delta_start_time(daysago = 1, hoursago=0)

# let the user know the program started
print("Starting ZenDesk ticket pull.")

try:
    # Pull the first page of tickets
    response = zd.incremental_ticket_pull(start_time)

    # handle the initial responses if no tickets were returned; if we timed out, let's try again
    if response.status_code == 429:
        zd.status_handler(response)
        response = zd.incremental_ticket_pull(start_time)
    else:
        zd.status_handler(response)

except ValueError:
    print("Reached most current ticket.")

# simple counter
success = 1

# create the files we'll be writing to'
# change to 'a+' if new tickets need to be appended and not overwritten
zendump = open('zendump.csv', 'w+')
log = open('log.txt', 'a+')

# get the necessary information from the response
zdresult = response.json()
tickets = zdresult['results']

# get the headers from the tickets response
header = zdresult['field_headers']

# create the objects that will let us write to the files
# change the delimiter as needed; beware that the results do have free-text, so a comma may not work
csvwriter = csv.DictWriter(zendump, delimiter='~', quoting=csv.QUOTE_ALL, fieldnames=header)
if os.stat('zendump.csv').st_size <= 0:
    csvwriter.writeheader()

# handle and write the data while there is data
try:

    # continue looping until we have all tickets
    while zdresult['end_time'] != '':
        # write tickets to file
        for ticket in tickets:
            csvwriter.writerow({k: smart_str(v) for k, v in ticket.items()})

        # write our current location to the file
        log.write(str(zdresult['end_time']) + '\n')

        # get the next page of tickets
        response = zd.incremental_ticket_pull(zdresult['end_time'])

        # handle the response
        if response.status_code == 429:
            zd.status_handler(response)
            response = zd.incremental_ticket_pull(zdresult['end_time'])

        success += 1
        print("Page " + str(success) + " Successful.")
        print('new_endtime: ' + str(zdresult['end_time']))

        # get the actual ticket data
        zdresult = response.json()
        tickets = zdresult['results']

# handle the error we reach when there is no more data, hence no more tickets
except ValueError:
    print("Reached most current ticket.")

    # free up the system resources we took to write to the files
    zendump.close()
    log.close()
