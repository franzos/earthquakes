import json
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def mk_vector(p1: Point, p2: Point):
    return {'x': (p2.x - p1.x), 'y': (p2.y - p1.y)}


def mk_dot(u, v):
    return u['x'] * v['x'] + u['y'] * v['y']


def point_in_rectangle(point: Point, recta: dict):
    '''Simplistic approach that assumes all corners are 90 degrees'''
    AB = mk_vector(recta['NW'], recta['NE'])
    AM = mk_vector(recta['NW'], point)
    BC = mk_vector(recta['NE'], recta['SW'])
    BM = mk_vector(recta['NE'], point)

    return 0 <= mk_dot(AB, AM) <= mk_dot(AB, AB) \
        and 0 <= mk_dot(BC, BM) <= mk_dot(BC, BC)


def main():
    html_file = "ipma_data/sismicidade.html"
    html_content = open(html_file).read()

    soup = BeautifulSoup(html_content, 'html.parser')
    data = json.loads(
                re.search(
                    r'var seismicdata_world = ({.*})', html_content
                ).group(1))

    # Initial loop; Check what we've got

    date_start = 0
    date_end = 0
    count = len(data['data'])

    for entry in data['data']:
        # format 2023-12-10T11:52:51
        date = datetime.strptime(entry['time'], '%Y-%m-%dT%H:%M:%S')
        if date_start == 0:
            date_start = date
        if date_end == 0:
            date_end = date
        if date_end < date:
            date_end = date
        if date_start > date:
            date_start = date

    print("Got %s entries from %s to %s" % (count, date_start, date_end))

    # Second loop; Filter data by region

    region_rectangle = {
        'NW': Point(42.30, -10.30),
        'NE': Point(42.30, -6.30),
        'SW': Point(36.30, -10.30),
        'SE': Point(36.30, -6.30)
    }

    data_in_region = []
    exclude_count = 0

    for entry in data['data']:
        point = Point(float(entry['lat']), float(entry['lon']))
        in_region = point_in_rectangle(point, region_rectangle)
        if in_region:
            data_in_region.append(entry)
        else:
            exclude_count += 1

    print("Got %s entries in region; %s entries have been excluded."
          % (len(data_in_region), exclude_count))

    # Sort by 7-day interval

    periods = []
    interval_hours = 168

    total_time = date_end - date_start
    total_time_hours = total_time.days * 24 + total_time.seconds / 3600
    intervals = total_time_hours / interval_hours

    for i in range(0, int(intervals)):
        start = date_start + timedelta(hours=i * interval_hours)
        end = start + timedelta(hours=interval_hours)
        periods.append({'#': i, 'start': start, 'end': end})

    for period in periods:
        period['entries'] = []

    for entry in data_in_region:
        time = datetime.strptime(entry['time'], '%Y-%m-%dT%H:%M:%S')
        for period in periods:
            if period['start'] <= time <= period['end']:
                period['entries'].append(entry)
                break

    plot_labels = []
    plot_data = []

    for period in periods:
        count = len(period['entries'])
        plot_labels.append(period['#'])
        plot_data.append(count)

    import plotext

    plotext.bar(plot_labels, plot_data, orientation="vertical", width=3/5)
    plotext.title("Number of earthquakes, by week")
    plotext.show()


if __name__ == '__main__':
    main()
