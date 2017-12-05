import argparse
import concurrent.futures
from time import strftime, time, localtime

import requests

BASE_URL = 'https://api.flightradar24.com/common/v1/airport.json'
HEADERS = {'user-agent': 'my-app/0.0.1'}
TPL = """Airport: {name}
ICAO Code: {icao_code}

Weather: {weather}

Arrivals: {arrivals}

Departures: {departures}
"""


class Airport(object):
    def __init__(self, icao_code):
        self.url = '{}?code={}&timestamp={}'.format(BASE_URL,
                                                    icao_code,
                                                    int(time()))
        self.name = ''
        self.icao_code = icao_code
        self.arrivals = []
        self.departures = []
        self.weather = {}
        self.data = {}

    def load_url(self):
        try:
            resp = requests.get(self.url, headers=HEADERS)
            if resp.ok:
                jdata = resp.json()
                self.data = jdata['result']['response']['airport']['pluginData']
        except Exception as e:
            print('Fail to load data: {}'.format(e))

    def fetch_data(self):
        try:
            self.name = self.data.get('details', {}).get('name')
            for flight in self.data.get('schedule', {}).get('arrivals', {}).get('data', []):
                self.arrivals.append(self._get_flight_data(flight))
            for flight in self.data.get('schedule', {}).get('departures', {}).get('data', []):
                self.departures.append(self._get_flight_data(flight))
            self.weather = self.data.get('weather', {})

        except Exception as e:
            print('Fail to fetch data with error: {}'.format(e))

    def _get_flight_data(self, flight):
        return {'number': flight.get('flight', {}).get('identification', {}).get('number', {}).get('default'),
                'status':  flight.get('flight', {}).get('status', {}).get('text'),
                'departure': strftime('%Y-%m-%d %H:%M:%S', localtime(flight.get('flight', {}).get('time', {}).get('scheduled', {}).get('departure'))),
                'arrival': strftime('%Y-%m-%d %H:%M:%S', localtime(flight.get('flight', {}).get('time', {}).get('scheduled', {}).get('arrival')))}

    def __str__(self):
        return TPL.format(name=self.name, weather=self.weather,
                          arrivals=self.arrivals, departures=self.departures,
                          icao_code=self.icao_code)


if __name__ == '__main__':
    usage = "--narg [comaseperateed icao codes]"

    parser = argparse.ArgumentParser(usage=usage)
    parser.add_argument('--nargs', nargs='+', action="store",
                        dest="airports",
                        help="Use --nargs icao codes ")
    airports = parser.parse_args().airports

    if airports:
        airport_list = []
        for airport in airports:
            port = Airport(airport)
            airport_list.append(port)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(port.load_url): port for port in airport_list}

        for port in airport_list:
            port.fetch_data()
        airport_list.sort(key=lambda airport: airport.weather.get('wind', {}).get('speed', {}).get('kmh', 0))

        for airport in airport_list:
            print(airport)
    else:
        print('Use --nargs and icao_codes')
