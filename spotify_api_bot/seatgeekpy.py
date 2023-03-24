from datetime import datetime, timedelta
import json
import logging

import requests
from yaml import load, Loader

class SeatgeekBot():

    def __init__(
            self,
            client_id : str,
            client_secret : str,
            input_artists : list,
            output_file : str,
            log
            ):
        
        self.client_id      = client_id
        self.client_secret  = client_secret

        self.input_artists  = input_artists

        self.output_file    = output_file
        if '.json' not in self.output_file:
            self.output_file = self.output_file + '.json'
        log.info(f'Will save output json data to {self.output_file}')

        self.log = log

        self.data = {
            'meta' : {'lastsync' : datetime.now().strftime('%Y%m%d')},
            'artists' : {}
        }

    def send_request(self, client_id, client_secret, artist):
        request_string = f'https://api.seatgeek.com/2/events?client_id={client_id}&client_secret={client_secret}&performers.slug={artist}&venue.state=AZ'
        response = requests.get(request_string)
        return response, response.json()
    
    def get_events(self):
        response_codes = []
        self.log.info('Looking for events from the interested artists')
        for artist in self.input_artists:
            artist_formatted = artist.replace(' ', '-').lower()
            code, self.data['artists'][artist] = self.send_request(
                self.client_id, self.client_secret, artist_formatted
                )
            self.log.info(f' {artist} events coming up: {self.data["artists"][artist]["meta"]["total"]}')
            if self.data['artists'][artist]["meta"]["total"] > 0:
                utc_date = datetime.strptime(self.data['artists'][artist]['events'][0]['datetime_utc'], '%Y-%m-%dT%H:%M:%S')
                az_date  = utc_date - timedelta(hours=7)
                self.data['artists'][artist]['events'][0]['datetime_az'] = az_date.strftime('%Y-%m-%d')
            response_codes.append(code)
        return response_codes
    
    def write_output(self):
        self.log.info(f'Writing json data to {self.output_file}')
        with open(self.output_file, 'w') as outfile:
            json.dump(self.data, outfile, indent=4)

    def run(self):
        codes = self.get_events()
        self.write_output()
        return codes
        
    
if __name__ == '__main__':

    log = logging.getLogger(__name__)

    config = None
    with open('config.yaml', 'r') as yml:
        config = load(yml, Loader=Loader)['seatgeek']
    
    seatgeekbot = SeatgeekBot(
        config['client_id'],
        config['client_secret'],
        config['manual_artists'],
        config['output_file_path'],
        log
    )
    seatgeekbot.run()