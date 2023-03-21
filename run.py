import json
import logging
import yaml

import spotipy

from auth import get_oauth

print('Grabbing authentication from spotify...')
spotify = get_oauth()
print('Successfully connected to the api!')

artist_list = []
offset = 0
while True:
    data = spotify.playlist_tracks('5WQ3UPX8rxzDaIdC1JjNlg', limit=11, offset=offset, fields='items.track.artists')
    if data['items'] == []:
        break
    for i in data['items']:
        artist = i['track']['artists'][0]['name']
        if artist not in artist_list:
            artist_list.append(artist)
    offset += 10

print(artist_list)
print(len(artist_list))


with open('/data/sample_data.json', 'w') as outfile:
    print('Writing data to an output json file')
    json.dump(data, outfile, indent=4)