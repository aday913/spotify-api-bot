from datetime import datetime, timedelta
import json
import logging
import os
import time
import sqlite3
import sys

from dotenv import load_dotenv
import requests


class SeatgeekBot:

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        input_artists: list,
        concert_db: str,
        state: str,
        log,
    ):
        """_summary_

        Args:
            client_id (str): Seatgeek api client ID
            client_secret (str): Seatgeek api client secret
            input_artists (list): list of strings of input artists to search for events for
            concert_db (str): name/path of sqlite database to store events
            log: logging logger object
        """

        self.client_id = client_id
        self.client_secret = client_secret

        self.input_artists = input_artists

        self.output_file = concert_db
        if ".db" not in self.output_file:
            self.output_file = self.output_file + ".db"
        log.info(f"Will save output json data to {self.output_file}")
        
        log.info(f"Connecting to concert database {self.output_file}")
        self.conn = sqlite3.connect(self.output_file)
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS concerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artist TEXT,
                event_date TEXT,
                venue TEXT,
                city TEXT,
                state TEXT,
                UNIQUE(artist, event_date, venue, city, state)
            )
            """
        )
        log.info(f"Successfully connected to concert database {self.output_file}")

        self.state = state

        self.log = log

        self.data = {
            "meta": {"lastsync": datetime.now().strftime("%Y%m%d")},
            "artists": {},
        }

    def send_request(self, client_id, client_secret, artist):
        request_string = f"https://api.seatgeek.com/2/events?client_id={client_id}&client_secret={client_secret}&performers.slug={artist}&venue.state={self.state}"
        response = requests.get(request_string)
        return response, response.json()

    def get_events(self):
        response_codes = []
        self.log.info("Looking for events from the interested artists")
        for artist in self.input_artists:
            try:
                artist_formatted = artist.replace(" ", "-").lower()
                self.data["meta"] = {"lastsync": datetime.now().strftime("%Y%m%d")}
                code, self.data["artists"][artist] = self.send_request(
                    self.client_id, self.client_secret, artist_formatted
                )

                self.log.info(
                    f' {artist} events coming up: {self.data["artists"][artist]["meta"]["total"]}'
                )
                if self.data["artists"][artist]["meta"]["total"] > 0:
                    utc_date = datetime.strptime(
                        self.data["artists"][artist]["events"][0]["datetime_utc"],
                        "%Y-%m-%dT%H:%M:%S",
                    )
                    local_date = utc_date - timedelta(hours=7)
                    self.data["artists"][artist]["events"][0]["datetime_local"] = (
                        local_date.strftime("%Y-%m-%d")
                    )
                response_codes.append(code)
            except Exception as error:
                self.log.error(
                    f"Got the following error when getting event for artist {artist_formatted}: {error}"
                )
                self.data["artists"].pop(
                    artist
                )  # Remove the error-prone artist from the output data
            time.sleep(3)  # Sleep for a second to avoid hitting API rate limits
        return response_codes

    def write_output(self):
        self.log.info(f"Writing output to {self.output_file}")
        for artist in self.data["artists"]:
            if self.data["artists"][artist]["meta"]["total"] == 0:
                continue
            for event in self.data["artists"][artist]["events"]:
                try:
                    self.cursor.execute(
                        "INSERT OR IGNORE INTO concerts (artist, event_date, venue, city, state) VALUES (?, ?, ?, ?, ?)",
                        (
                            artist,
                            event["datetime_local"],
                            event["venue"]["name"],
                            event["venue"]["city"],
                            event["venue"]["state"],
                        ),
                    )
                except Exception as error:
                    self.log.error(
                        f"Got the following error when writing to database for artist {artist}: {error}"
                    )
        self.conn.commit()

    def run(self):
        codes = self.get_events()
        self.write_output()
        self.conn.close()
        return codes


if __name__ == "__main__":

    log = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s-%(levelname)s: %(message)s"
    )

    if os.path.exists(".env"):
        log.info("Loading environment variables from .env file")
        load_dotenv()

    config = {}
    required_vars = [
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

    if not os.path.exists(config["ARTIST_DB"]):
        log.error(f"Artist database {config['ARTIST_DB']} does not exist.")
        sys.exit(1)

    conn = sqlite3.connect(config["ARTIST_DB"])
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM artists")
    interested_artists = [row[0] for row in cursor.fetchall()]
    conn.close()

    spotifybot = SeatgeekBot(
        config["SEATGEEK_CLIENT_ID"],
        config["SEATGEEK_CLIENT_SECRET"],
        interested_artists,
        config["CONCERT_DB"],
        config["STATE_CODE"],
        log,
    )
    spotifybot.run()
