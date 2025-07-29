import json
import logging
import os
import sys

from dotenv import load_dotenv

from spotify_api_bot.botipy import SpotifyBot
from spotify_api_bot.seatgeekpy import SeatgeekBot

log = logging.getLogger(__name__)

# Main function to orchestrate the bot operations
def main(config):
    # Extract and log Spotify configuration variables
    log.info("Parsing spotify configuration variables")
    spotify_ci = config['SPOTIFY_CLIENT_ID']
    spotify_cs = config['SPOTIFY_CLIENT_SECRET']
    spotify_redirect = config['SPOTIFY_REDIRECT_URI']
    spotify_concert = config['SPOTIFY_PLAYLIST_ID']

    log.info("Parsing seatgeek configuration variables")
    seatgeek_ci = config['SEATGEEK_CLIENT_ID']
    seatgeek_cs = config['SEATGEEK_CLIENT_SECRET']
    output_file = config['OUTPUT_FILE_DESTINATION']
    state_id = config['STATE_CODE']

    if ".json" not in output_file:
        output_file = output_file + ".json"

    log.info("Initializing instance of the spotify bot")
    spotifybot = SpotifyBot(
        spotify_ci, spotify_cs, spotify_redirect, spotify_concert, log
    )
    interested_artists = spotifybot.run()

    log.info("Initializing instance of the seatgeek bot")
    seatgeekbot = SeatgeekBot(
        seatgeek_ci, seatgeek_cs, interested_artists, output_file, state_id, log
    )
    response_codes = seatgeekbot.run()  # Run the Seatgeek bot and collect response codes

    # Read the output file to load event data
    with open(output_file, "r") as f:
        data = json.load(f)

    # Log and display a list of artists with upcoming events
    log.info("Below are a list of the artists that have events coming up:")
    for artist in data["artists"]:
        if data["artists"][artist]["meta"]["total"] > 0:
            event_date = data["artists"][artist]["events"][0]["datetime_utc"]
            event_city = data["artists"][artist]["events"][0]["venue"]["city"]
            event_venue = data["artists"][artist]["events"][0]["venue"]["name"]
            all_performers = [
                i["name"] for i in data["artists"][artist]["events"][0]["performers"]
            ] 
            log.info(
                f"  {artist}: {event_date} in {event_city} at {event_venue}. All performers: {all_performers}"
            )


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s-%(levelname)s: %(message)s"
    )

    log = logging.getLogger(__name__)

    config = {}

    if os.path.exists('.env'):
        log.info("Loading environment variables from .env file")
        load_dotenv()

    required_vars = [
        'SPOTIFY_CLIENT_ID',
        'SPOTIFY_CLIENT_SECRET',
        'SPOTIFY_REDIRECT_URI',
        'SPOTIFY_PLAYLIST_ID',
        'SEATGEEK_CLIENT_ID',
        'SEATGEEK_CLIENT_SECRET',
        'OUTPUT_FILE_DESTINATION',
        'STATE_CODE'
    ]
    for var in required_vars:
        logging.info(f"Checking environment variable: {var}")
        logging.info(f"Environment variable {var} is set to: {os.environ.get(var)}")
        if var not in os.environ:
            log.error(f"Environment variable {var} is not set.")
            sys.exit(1)
        config[var] = os.environ[var]

    if os.environ.get('OUTPUT_FILE_DESTINATION'):
        config['OUTPUT_FILE_DESTINATION'] = os.environ['OUTPUT_FILE_DESTINATION']
    else:
        config['OUTPUT_FILE_DESTINATION'] = os.path.join(os.getcwd(), 'output.json')

    main(config)
