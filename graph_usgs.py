import os
import csv
from datetime import datetime, timedelta
from graph_ipma import Point, point_in_rectangle

'''
Files expected at usgs_data/*.csv
ex. data/2023-04-12 00:00:00_2023-05-12 00:00:00.csv

Will read all files and collect all data in an array for plot.

CSV Columns
    time
    latitude
    longitude
    depth
    mag
    magType
    nst
    gap
    dmin
    rms
    net
    id
    updated
    place
    type
    horizontalError
    depthError
    magError
    magNst
    status
    locationSource
    magSource

'''

DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
DATA_DIR = 'usgs_data'
FORMAT = 'csv'
LIMIT = 1000


region_rectangle = {
    'NW': Point(42.30, -130.30),
    'NE': Point(42.30, -110.30),
    'SW': Point(36.30, -130.30),
    'SE': Point(36.30, -110.30)
}


def main():
    files = []

    if os.path.isdir(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if filename.endswith(FORMAT):
                files.append(filename)

    if len(files) == 0:
        print("No files found")
        exit(1)

    data = []

    count = 0
    for filename in files:
        with open(DATA_DIR + '/' + filename) as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)

        count += 1
        if count == LIMIT:
            break

    if len(data) == 0:
        print("No data found")
        exit(1)

    date_start = 0
    date_end = 0
    exclude_count = 0

    data_in_region = []

    for entry in data:
        # fomat: 2022-10-13T23:59:54.158Z
        date = datetime.strptime(entry['time'], DATE_FORMAT)
        if date_start == 0:
            date_start = date
        if date_end == 0:
            date_end = date
        if date_end < date:
            date_end = date
        if date_start > date:
            date_start = date

        point = Point(float(entry['latitude']), float(entry['longitude']))
        # print("%s - %s" % (point.x, point.y))
        in_region = point_in_rectangle(point, region_rectangle)
        if in_region:
            data_in_region.append(entry)
        else:
            exclude_count += 1

    print("Got %s entries from %s to %s; %s have been excluded"
          % (len(data_in_region), date_start, date_end, exclude_count))

    periods = []
    interval_hours = 720

    total_time = date_end - date_start
    total_time_hours = total_time.total_seconds() / 3600
    intervals = total_time_hours / interval_hours

    for i in range(0, int(intervals)):
        start = date_start + timedelta(hours=i * interval_hours)
        end = start + timedelta(hours=interval_hours)
        periods.append({'#': i, 'start': start, 'end': end, 'mag': 0, 'depth': 0})

    for period in periods:
        period['entries'] = []

    max_mag = 0
    max_depth = 0
    for entry in data_in_region:
        time = datetime.strptime(entry['time'], DATE_FORMAT)
        for period in periods:
            if period['start'] <= time <= period['end']:
                period['entries'].append(entry)
                entry_mag = float(entry['mag'])
                if entry_mag > period['mag']:
                    period['mag'] = entry_mag
                if entry_mag > max_mag:
                    max_mag = entry_mag

                entry_depth = float(entry['depth'])
                if entry_depth > period['depth']:
                    period['depth'] = entry_depth
                if entry_depth > max_depth:
                    max_depth = entry_depth

                break

    plot_labels = []
    plot_data = []
    plot_data_mag = []
    plot_data_depth = []

    max_quakes = 0
    for period in periods:
        count = len(period['entries'])
        if count > max_quakes:
            max_quakes = count

    for period in periods:
        count = len(period['entries'])
        plot_labels.append(period['#'])
        plot_data.append(count / max_quakes * 100)
        plot_data_mag.append(period['mag'] / max_mag * 100)
        plot_data_depth.append(period['depth'] / max_depth * 100)

    import plotext

    plotext.multiple_bar(
            plot_labels,
            [plot_data, plot_data_mag, plot_data_depth],
            label=['Quakes', 'Max Mag.', 'Max Depth'],
            )
    plotext.title("Number of earthquakes and intensity, by month, %s - %s"
                  % (date_start, date_end))
    plotext.show()


if __name__ == '__main__':
    main()
