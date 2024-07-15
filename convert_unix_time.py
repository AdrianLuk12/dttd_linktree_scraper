import datetime

# Convert the timestamp to seconds
timestamp_seconds = 1636288616000 / 1000

# Convert the timestamp to a datetime object
date_time = datetime.datetime.fromtimestamp(timestamp_seconds)

print(date_time)