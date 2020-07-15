import spotipy
import sys
from spotipy.oauth2 import SpotifyOAuth
import argparse
import json
import jsondb
from tqdm import tqdm
import os

DEFAULT_LIMIT = 50
MAX_TRACKS = 3000

parser = argparse.ArgumentParser(description="spotify fav exporter")
parser.add_argument("spotify_client_id", type=str)
parser.add_argument("spotify_client_secret", type=str)
parser.add_argument("--save", type=str)
args = parser.parse_args()

scope = "user-library-read"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
  scope=scope, 
  client_id="b53ccc15f577423caac3f8a660e29ed5", 
  client_secret="d10e36f75bc8475196cd846a34d4fa6b", 
  redirect_uri="http://localhost:9000",
  cache_path=".spotify-cache"
))

current_track = 0
final_tracks = []
progressbar = tqdm(range(0, MAX_TRACKS), unit=" tracks")
while current_track < MAX_TRACKS:
  results = sp.current_user_saved_tracks(limit=DEFAULT_LIMIT, offset=current_track)
  if len(results['items']) <= 0:
    break

  current_track += len(results['items'])
  progressbar.update(len(results['items']))

  for idx, item in enumerate(results['items']):
    track = item['track']
    final_track = { 
      "added_at": item["added_at"],
      "artists": [x['name'] for x in track['artists']],
      "name": track['name'],
      "album": track["album"]["name"],
      "spotify_id": track["id"],
    }
    final_tracks.append(final_track)

print(f"total found: {len(final_tracks)}")
final_tracks.reverse()

if args.save != None:
  os.remove(args.save)
  db = jsondb.Database(args.save)
  dict_db = { idx: item for idx, item in enumerate(final_tracks) }
  db.data(dictionary=dict_db)
  print(f'file {args.save} saved with {len(final_tracks)} tracks')
else:
  print(f'try start script with --save flag eg: python spotify-export.py --save export-file.txt')