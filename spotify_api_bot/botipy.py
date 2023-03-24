from datetime import datetime
import logging
# import os

# from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from yaml import load, Loader

class SpotifyBot():
    
    def __init__(
            self, 
            client_id : str, 
            client_secret : str, 
            redirect : str, 
            discover_playlist_id : str,
            save_playlist_id : str,
            concert_check_id : str,
            output_file_path: str
    ):
        """Saves a playlists arsists to an output file

        Args:
            client_id (str): spotify api client id
            client_secret (str): spotify api client secret
            redirect (str): spotify api redirect uri
            discover_playlist_id (str): discover weekly playlist id
            save_playlist_id (str): discover weekly saved playlist id
            concert_check_id (str): concert artists playlist id
            output_file_path (str): output artists file path
        """
        # Authorization variables
        self.client_id      = client_id
        self.client_secret  = client_secret
        self.redirect       = redirect

        # Discovery weekly automation variables
        self.discover_playlist_id   = discover_playlist_id
        self.discover_save_id       = save_playlist_id

        # Artist check automation variables
        self.concert_id = concert_check_id
        self.output_path = output_file_path

        self.spotify = self.get_oath(
            self.client_id, 
            self.client_secret, 
            self.redirect
            )
            
    def get_oath(self, id, secret, redirect):
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
                open_browser=False
            )
        )
    
    def get_concert_artists(self):
        artist_list = []
        offset = 0
        while True:
            data = self.spotify.playlist_tracks(
                self.concert_id, 
                limit=11, 
                offset=offset, 
                fields='items.track.artists'
                )
            if data['items'] == []:
                break
            for i in data['items']:
                artist = i['track']['artists'][0]['name']
                if artist not in artist_list:
                    artist_list.append(artist)
            offset += 10
        return artist_list
    
    def write_to_file(self):
        with open(self.output_path, 'w') as outfile:
            outfile.write('\n'.join(self.concert_artists))
    
    def run(self):
        now = datetime.now()
        now_str = now.strftime('%Y%m%d')
        self.concert_artists = [now_str] + self.get_concert_artists()
        self.write_to_file()

if __name__ == '__main__':

    log = logging.getLogger(__name__)
    
    config = None
    with open('config.yaml', 'r') as yml:
        config = load(yml, Loader=Loader)['config']
    
    spotifybot = SpotifyBot(
        config['client_id'],
        config['client_secret'],
        config['redirect_url'],
        config['discover_weekly_id'],
        config['discover_save_id'],
        config['concert_playlist_id'],
        config['output_file_path']
    )

    spotifybot.run()