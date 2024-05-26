from datetime import datetime
import logging

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from yaml import load, Loader


class SpotifyBot:

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect: str,
        concert_check_id: str,
        log,
    ):
        """Saves a playlists arsists to an output file

        Args:
            client_id (str): spotify api client id
            client_secret (str): spotify api client secret
            redirect (str): spotify api redirect uri
            concert_check_id (str): concert artists playlist id
            output_file_path (str): output artists file path
        """
        # Authorization variables
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect = redirect

        # Artist check automation variables
        self.concert_id = concert_check_id

        self.log = log

        self.spotify = self.get_oath(self.client_id, self.client_secret, self.redirect)
        self.log.info("Successfully authorized myself for the spotify api")

    def get_oath(self, id, secret, redirect):
        self.log.info("Getting authentication for spotify api")
        # Scopes found in spotipy documentation
        SCOPES = [
            "user-library-modify",
            "user-library-read",
            "user-top-read",
            "user-read-recently-played",
            "playlist-read-private",
            "playlist-read-collaborative",
            "playlist-modify-private",
            "playlist-modify-public",
        ]

        return spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=id,
                client_secret=secret,
                # set up in spotify dev dashboard as redirect uri
                redirect_uri=redirect,
                scope=SCOPES,
                open_browser=False,
            )
        )

    def get_concert_artists(self):
        self.log.info("Getting all artists from concert playlist")
        artist_list = []
        offset = 0
        while True:
            data = self.spotify.playlist_tracks(
                self.concert_id, limit=11, offset=offset, fields="items.track.artists"
            )
            if data["items"] == []:
                break
            for i in data["items"]:
                artist = i["track"]["artists"][0]["name"]
                if artist not in artist_list:
                    self.log.info(f" Found artist {artist}")
                    artist_list.append(artist)
            offset += 10
        self.log.info(f"Total amount of artists found in playlist: {len(artist_list)}")
        return artist_list

    def run(self) -> list:
        self.concert_artists = self.get_concert_artists()
        return self.concert_artists


if __name__ == "__main__":

    log = logging.getLogger(__name__)

    config = None
    with open("config.yaml", "r") as yml:
        config = load(yml, Loader=Loader)["spotify"]

    spotifybot = SpotifyBot(
        config["client_id"],
        config["client_secret"],
        config["redirect_url"],
        config["concert_playlist_id"],
        log,
    )

    artists = spotifybot.run()
    print(artists)
