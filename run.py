import json
import logging
import os
import sqlite3
import sys

from dotenv import load_dotenv

from spotify_api_bot.botipy import SpotifyBot
from spotify_api_bot.seatgeekpy import SeatgeekBot

log = logging.getLogger(__name__)


def main(config):
    # Extract and log Spotify configuration variables
    log.info("Parsing spotify configuration variables")
    spotify_ci = config["SPOTIFY_CLIENT_ID"]
    spotify_cs = config["SPOTIFY_CLIENT_SECRET"]
    spotify_redirect = config["SPOTIFY_REDIRECT_URI"]
    spotify_concert = config["SPOTIFY_PLAYLIST_ID"]
    artist_db = config["ARTIST_DB"]

    log.info("Parsing seatgeek configuration variables")
    seatgeek_ci = config["SEATGEEK_CLIENT_ID"]
    seatgeek_cs = config["SEATGEEK_CLIENT_SECRET"]
    concert_db = config["CONCERT_DB"]
    state_id = config["STATE_CODE"]

    if ".db" not in artist_db:
        artist_db = artist_db + ".db"
    if ".db" not in concert_db:
        concert_db = concert_db + ".db"

    log.info("Initializing instance of the spotify bot")
    spotifybot = SpotifyBot(
        spotify_ci, spotify_cs, spotify_redirect, spotify_concert, artist_db, log
    )
    interested_artists = spotifybot.run()

    log.info("Initializing instance of the seatgeek bot")
    seatgeekbot = SeatgeekBot(
        seatgeek_ci, seatgeek_cs, interested_artists, concert_db, state_id, log
    )
    # Run the Seatgeek bot and collect response codes
    _ = (
        seatgeekbot.run()
    )  

    # Print the events found for each artist to the console
    conn = sqlite3.connect(concert_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM concerts")
    concerts = cursor.fetchall()
    conn.close()
    for concert in concerts:
        log.info(
            f"Found concert for artist {concert[1]} at {concert[2]} on {concert[3]} in {concert[4]}, {concert[5]}"
        )

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s-%(levelname)s: %(message)s"
    )

    log = logging.getLogger(__name__)

    config = {}

    if os.path.exists(".env"):
        log.info("Loading environment variables from .env file")
        load_dotenv()

    required_vars = [
        "SPOTIFY_CLIENT_ID",
        "SPOTIFY_CLIENT_SECRET",
        "SPOTIFY_REDIRECT_URI",
        "SPOTIFY_PLAYLIST_ID",
        "SEATGEEK_CLIENT_ID",
        "SEATGEEK_CLIENT_SECRET",
        "ARTIST_DB",
        "CONCERT_DB",
        "STATE_CODE",
    ]
    for var in required_vars:
        logging.info(f"Checking environment variable: {var}")
        logging.debug(f"Environment variable {var} is set to: {os.environ.get(var)}")
        if var not in os.environ:
            log.error(f"Environment variable {var} is not set.")
            sys.exit(1)
        config[var] = os.environ[var]

    main(config)
