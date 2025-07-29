from datetime import datetime, timedelta
import json
import logging
import os

import requests
from yaml import load, Loader


class SeatgeekBot:

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        input_artists: list,
        output_file: str,
        state: str,
        log,
    ):
        """_summary_

        Args:
            client_id (str): Seatgeek api client ID
            client_secret (str): Seatgeek api client secret
            input_artists (list): list of strings of input artists to search for events for
            output_file (str): name/path of output json file
            log: logging logger object
        """

        self.client_id = client_id
        self.client_secret = client_secret

        self.input_artists = input_artists

        self.output_file = output_file
        if ".json" not in self.output_file:
            self.output_file = self.output_file + ".json"
        log.info(f"Will save output json data to {self.output_file}")

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
        return response_codes

    def write_output(self):
        # First delete the old events file
        self.log.debug(f"Deleting old json file {self.output_file}")
        try:
            os.remove(self.output_file)
        except Exception:
            self.log.debug(
                f"Could not find existing file {self.output_file}, so cannot delete"
            )

        # Now write the events data to the output file
        self.log.info(f"Writing json data to {self.output_file}")
        with open(self.output_file, "w") as outfile:
            json.dump(self.data, outfile, indent=4)

    def run(self):
        codes = self.get_events()
        self.write_output()
        return codes


if __name__ == "__main__":

    log = logging.getLogger(__name__)

    config = None
    with open("config.yaml", "r") as yml:
        config = load(yml, Loader=Loader)["seatgeek"]

    seatgeekbot = SeatgeekBot(
        config["client_id"],
        config["client_secret"],
        config["manual_artists"],
        config["output_file_path"],
        config["state"],
        log,
    )
    seatgeekbot.run()
