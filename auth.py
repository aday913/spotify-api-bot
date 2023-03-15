import os

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

def get_oauth():
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

    load_dotenv()

    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')

    return spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID, 
            client_secret=CLIENT_SECRET, 
            # set up in spotify dev dashboard as redirect uri
            redirect_uri="http://localhost:5000/redirect", 
            scope=SCOPES, 
            open_browser=False
        )
    )
