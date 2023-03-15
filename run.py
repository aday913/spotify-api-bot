import json

import spotipy

from auth import get_oauth

print('Grabbing authentication from spotify...')
spotify = get_oauth()
print('Successfully connected to the api!')

print('Getting my saved tracks from the api')
data = spotify.current_user_saved_tracks()

with open('sample_data.json', 'w') as outfile:
    print('Writing data to an output json file')
    json.dump(data, outfile)