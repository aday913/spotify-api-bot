import json
import logging
import sys

from yaml import load, Loader

from spotify_api_bot.botipy import SpotifyBot
from spotify_api_bot.seatgeekpy import SeatgeekBot

def main(config, log):
    log.info('Parsing spotify configuration variables')
    spotify_ci          = config['spotify']['client_id']
    spotify_cs          = config['spotify']['client_secret']
    spotify_redirect    = config['spotify']['redirect_url']
    spotify_dw          = config['spotify']['discover_weekly_id']
    spotify_dws         = config['spotify']['discover_save_id']
    spotify_concert     = config['spotify']['concert_playlist_id']

    log.info('Parsing seatgeek configuration variables')
    seatgeek_ci         = config['seatgeek']['client_id']
    seatgeek_cs         = config['seatgeek']['client_secret']
    output_file         = config['seatgeek']['output_file_path']
    state_id            = config['seatgeek']['state_id']

    if '.json' not in output_file:
        output_file = output_file + '.json'

    log.info('Initializing instance of the spotify bot')
    spotifybot = SpotifyBot(
        spotify_ci,
        spotify_cs,
        spotify_redirect,
        spotify_dw,
        spotify_dws,
        spotify_concert,
        log
    )
    interested_artists = spotifybot.run()

    log.info('Initializing instance of the seatgeek bot')
    seatgeekbot = SeatgeekBot(
        seatgeek_ci,
        seatgeek_cs,
        interested_artists,
        output_file,
        state,
        log
    )
    response_codes = seatgeekbot.run()

    with open(output_file, 'r') as f:
        data = json.load(f)
    
    log.info('Below are a list of the artists that have events coming up:')
    for artist in data['artists']:
        if data['artists'][artist]['meta']['total'] > 0:
            event_date = data["artists"][artist]["events"][0]["datetime_utc"]
            event_city = data["artists"][artist]["events"][0]["venue"]["city"]
            event_venue = data["artists"][artist]["events"][0]["venue"]["name"]
            all_performers = [ i["name"] for i in data["artists"][artist]["events"][0]["performers"] ]
            average_price = data["artists"][artist]["events"][0]["stats"]["average_price"]
            lowest_price = data["artists"][artist]["events"][0]["stats"]["lowest_price"]
            log.info(f'  {artist}: {event_date} in {event_city} at {event_venue} for as low as {lowest_price}, average price {average_price}. All performers: {all_performers}')

if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO, format='%(asctime)s-%(levelname)s: %(message)s')

    log = logging.getLogger(__name__)

    config = None
    log.info('Reading configuration file')
    try:
        with open('config.yaml', 'r') as yml:
            config = load(yml, Loader=Loader)
        log.info('Successfully read config.yaml')
    except Exception as error:
        log.error(f'Could not find configuration file of name "config.yaml"')
        sys.exit()
    
    main(config, log)
