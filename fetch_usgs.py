'''Fetch USGS earthquake data'''

import requests
import argparse
import time
from datetime import datetime, timedelta


'''
Example, 1 month, min. magnitude 0, order by time, format csv

GET https://earthquake.usgs.gov/fdsnws/event/1/query.csv?
    starttime=2023-12-08 00:00:00&
    endtime=2024-01-07 23:59:59&
    minmagnitude=0&
    orderby=time
'''

BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query.csv"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT_PARSER = "%Y-%m-%d"
OUT_DIR = 'usgs_data'


parser = argparse.ArgumentParser()
parser.add_argument('-m', '--months', type=int, default=1,
                    help="Number of months to fetch")
parser.add_argument('-s', '--start', type=str,
                    default=datetime.now().strftime(DATE_FORMAT_PARSER),
                    help="Start date from which to count backwards in months")
parser.add_argument('-t', '--timeout', type=int, default=10,
                    help="Timeout in seconds between requests")
parser.add_argument('-d', '--demo', type=int, default=1,
                    help="Demo (print url only)")

args = parser.parse_args()

months_to_fetch = args.months
start_date = datetime.strptime(args.start, DATE_FORMAT_PARSER)
is_demo = args.demo == 1


def make_filename(start_date: datetime, end_date: datetime):
    return f"{end_date.strftime(DATE_FORMAT)}_{start_date.strftime(DATE_FORMAT)}.csv"


if not is_demo:
    import os
    if not os.path.exists(OUT_DIR):
        os.mkdir(OUT_DIR)


# We will get some duplicates between months; we'll filter them later
range_start_date = start_date
for i in range(months_to_fetch):
    end_date = range_start_date - timedelta(days=30)
    filename = make_filename(range_start_date, end_date)

    url = BASE_URL
    url += f"?starttime={end_date.strftime(DATE_FORMAT)}&"
    url += f"endtime={range_start_date.strftime(DATE_FORMAT)}&"
    url += "minmagnitude=0&"
    url += "orderby=time"

    print("Fetching %s" % url)

    if is_demo:
        print("  [DEMO] Would write to %s" % f"{OUT_DIR}/{filename}")
    else:
        r = requests.get(url, timeout=args.timeout)
        r.raise_for_status()
        with open(f"{OUT_DIR}/{filename}", 'w') as f:
            f.write(r.text)
            print("  Wrote to %s" % f"{OUT_DIR}/{filename}")

    range_start_date = end_date

    print("   Timeout for %d seconds" % args.timeout)
    time.sleep(args.timeout)


print("Done!")
