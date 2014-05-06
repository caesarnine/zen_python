zen_python
==========

#### A library to access the ZenDesk API. Example code below to access the incremental API.

Install the library.
```
sudo pip install Zen
```

Import the library.
```python
import zen
```

Initialize the object.
```python
zd = zen.ZenDesk('https://enter_your_zendesk_url_here/api/v2',
             'enter_your_login_email_here/token',
             'enter your API token here')
```

Set the start time, the date in Unix epoch time we want to start pulling tickets from. In this example we'll assume we are pulling new tickets since the last update, so we're reading in the last time from the logfile.

```python
start_time = zd.last_log_time("log.txt")

# alternatively you can specify a time manually, or a time a certain number of days and/or hours ago:
# start_time = zd.delta_start_time(daysago = 1, hoursago=0)
```

Let the user know the program has started, and handle the initial page of data.

```python
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
```

Write that initial page of data, and continue following the pagination until we have no data, writing each page to file as we go.

```python
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
```
