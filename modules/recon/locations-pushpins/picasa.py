import module
# unique to module
from datetime import datetime
import math

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT latitude || \',\' || longitude FROM locations WHERE latitude IS NOT NULL AND longitude IS NOT NULL')
        self.register_option('radius', 1, True, 'radius in kilometers')
        self.info = {
                     'Name': 'Picasa Geolocation Search',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Searches Picasa for media in the specified proximity to a location.',
                     }
 
    def module_run(self, points):
        rad = self.options['radius']
        url = 'http://picasaweb.google.com/data/feed/api/all'
        count = 0
        new = 0
        kilometers_per_degree_latitude = 111.12
        for point in points:
            self.heading(point, level=0)
            lat = point.split(',')[0]
            lon = point.split(',')[1]
            # http://www.johndcook.com/blog/2009/04/27/converting-miles-to-degrees-longitude-or-latitude
            west_boundary = float(lon) - (math.cos(math.radians(float(lat))) * float(rad) / kilometers_per_degree_latitude)
            south_boundary = float(lat) - (float(rad) / kilometers_per_degree_latitude)
            east_boundary = float(lon) + (math.cos(math.radians(float(lat))) * float(rad) / kilometers_per_degree_latitude)
            north_boundary = float(lat) + (float(rad) / kilometers_per_degree_latitude)
            payload = {'alt': 'json', 'strict': 'true', 'bbox': '%.6f,%.6f,%.6f,%.6f' % (west_boundary, south_boundary, east_boundary, north_boundary)}
            processed = 0
            while True:
                resp = self.request(url, payload=payload)
                jsonobj = resp.json
                if not jsonobj:
                    self.error(resp.text)
                    break
                if not count: self.output('Collecting data for an unknown number of photos...')
                if not 'entry' in jsonobj['feed']: break
                for photo in jsonobj['feed']['entry']:
                    if not 'georss$where' in photo:
                        continue
                    source = 'Picasa'
                    screen_name = photo['author'][0]['name']['$t']
                    profile_name = photo['author'][0]['name']['$t']
                    profile_url = photo['author'][0]['uri']['$t']
                    media_url = photo['content']['src']
                    thumb_url = '/s72/'.join(media_url.rsplit('/', 1))
                    message = photo['title']['$t']
                    latitude = photo['georss$where']['gml$Point']['gml$pos']['$t'].split()[0]
                    longitude = photo['georss$where']['gml$Point']['gml$pos']['$t'].split()[1]
                    time = datetime.strptime(photo['published']['$t'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    new += self.add_pushpins(source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time)
                    count += 1
                processed += len(jsonobj['feed']['entry'])
                self.verbose('%s photos processed.' % (processed))
                qty = jsonobj['feed']['openSearch$itemsPerPage']['$t']
                start = jsonobj['feed']['openSearch$startIndex']['$t']
                next = qty + start
                if next > 1000: break
                payload['start-index'] = next
        self.summarize(new, count)
