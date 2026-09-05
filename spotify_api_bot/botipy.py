from datetime import datetime
import logging
import os
import sqlite3
import sys

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth


class SpotifyBot:

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect: str,
        spotify_playlist_id: str,
        artist_db: str,
        log,
    ):
        """Saves a playlists arsists to an output file

        Args:
            client_id (str): spotify api client id
            client_secret (str): spotify api client secret
            redirect (str): spotify api redirect uri
            concert_check_id (str): concert artists playlist id
            artist_db (str): name/path of sqlite database to store artists
            log: logging logger object
        """
        # Authorization variables
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect = redirect

        # Artist check automation variables
        self.spotify_playlist_id = spotify_playlist_id

        self.log = log

        self.log.info("Connecting to artist database")
        self.conn = sqlite3.connect(artist_db)
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS artists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                playlist_id TEXT
            )
            """
        )
        self.log.info("Successfully connected to artist database")

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
                self.spotify_playlist_id, limit=11, offset=offset, fields="items.track.artists"
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
        for artist in self.concert_artists:
            try:
                self.cursor.execute(
                    "INSERT INTO artists (name, playlist_id) VALUES (?, ?)",
                    (artist, self.spotify_playlist_id),
                )
                self.conn.commit()
                self.log.info(f"Added artist {artist} to database")
            except sqlite3.IntegrityError:
                self.log.warning(f"Artist {artist} already exists in database")
        self.conn.close()
        return self.concert_artists


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
        "SPOTIFY_CLIENT_ID",
        "SPOTIFY_CLIENT_SECRET",
        "SPOTIFY_REDIRECT_URI",
        "SPOTIFY_PLAYLIST_ID",
        "ARTIST_DB",
    ]
    for var in required_vars:
        logging.info(f"Checking environment variable: {var}")
        logging.debug(f"Environment variable {var} is set to: {os.environ.get(var)}")
        if var not in os.environ:
            log.error(f"Environment variable {var} is not set.")
            sys.exit(1)
        config[var] = os.environ[var]

    spotifybot = SpotifyBot(
        config["SPOTIFY_CLIENT_ID"],
        config["SPOTIFY_CLIENT_SECRET"],
        config["SPOTIFY_REDIRECT_URI"],
        config["SPOTIFY_PLAYLIST_ID"],
        config["ARTIST_DB"],
        log,
    )
    spotifybot.run()

