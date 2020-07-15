import tidalapi
import json
import logging as log
from tqdm import tqdm
from collections import OrderedDict
import jsondb
import argparse
import time

parser = argparse.ArgumentParser(description="tidal fav importer")
parser.add_argument("tidal_login", type=str, help="your tidal login")
parser.add_argument("tidal_password", type=str, help="your tidal password")
parser.add_argument("--load", type=str)
parser.add_argument("--clean", type=bool, default=False)
parser.add_argument("--confirm", type=bool, default=False)
parser.add_argument("--debug", type=bool, default=False)

# first + second (lazy) processing
parser.add_argument("--first_processing", type=bool, default=False)
parser.add_argument("--find_only_by_track_name", type=bool, default=False)
parser.add_argument("--process_not_founds", type=bool, default=False)
parser.add_argument("--ignore_artists_match", type=bool, default=False)

# manual processing
parser.add_argument("--manual_processing", type=bool, default=False)

# print what's left
parser.add_argument('--print_non_founds', type=bool, default=False)

# import library
parser.add_argument("--import_library", type=bool, default=False)

# 
args = parser.parse_args()

log.basicConfig(
    level=log.INFO if args.debug else log.WARNING,
    format='[%(asctime)s] (%(name)s %(levelname)s): %(message)s'
)

tidal = tidalapi.Session()
tidal.login(args.tidal_login, args.tidal_password)

### CLEAN FLAG
if args.clean:
  log.warning(f'are you sure going to remove {len(tidal.user.favorites.tracks())} tracks from your favorites on Tidal?')
  if not args.confirm:
    log.warning(f'pass --confirm flag')
    exit(1)
  else:
    log.warning(f'RUNNING TIDAL FAV CLEANUP')
    fav = tidal.user.favorites
    for track in tqdm(fav.tracks(), unit=" tracks"):
      tidal.user.favorites.remove_track(track.id)
    log.warning("COMPLETED")
    exit(0)

### LOAD FLAG
if not args.load:
  log.exception(f'you must supply flag --load eg: python import-tidal.py my@login my_password --load spotify-export.txt')
  exit(1)

### FUNCS
def format_tidal_track(track):
  return { 
    "artists": [x.name for x in track.artists],
    "album": track.album.name,
    "name": track.name,
    "tidal_id": track.id,
  }

def echo_track(track):
  return f'"{track.get("name", "")} -- {", ".join(track.get("artists", []))} -- {track.get("album", "")}"'

def track_equal(track1, track2, ignore_artists=False):
  mandatory_fields = ["name", "album", "artists"]
  for mf in mandatory_fields: 
    if not track1.get(mf, None):
      return None
    if not track2.get(mf, None):
      return None
  
  if  track1["name"].lower() == track2["name"].lower() and \
      track1["album"].lower() == track2["album"].lower():
        if not ignore_artists:
          if set([x.lower() for x in track1["artists"]]) == set([x.lower() for x in track2["artists"]]):
            return True
        else:
          return True

  return False

# first processing with 'skip when not found' policy
# sets tidal_id when exact match found otherwise None
def first_pricessing(database_path, find_only_by_track_name=False, process_not_founds=False, ignore_artists_match=False):
  sample_size = 2000

  db = jsondb.Database(database_path)
  # find only non-processed tracks
  if not process_not_founds:
    exported_tracks = {i: x for i, x in db.data().items() if "tidal_id" not in x.keys()}
  else:
    exported_tracks = {i: x for i, x in db.data().items() if "tidal_id" not in x.keys() or not x.get("tidal_id", None)}
  log.info(f'loaded: {len(exported_tracks.items())} unprocessed tracks')

  for saved_track_idx, saved_track in tqdm(exported_tracks.items(), unit=" track"):
    if saved_track.get("tidal_id", None) and not process_not_founds:
      pass
    log.info(f"looking for track:\t{echo_track(saved_track)}")
    if find_only_by_track_name:
      search_result = tidal.search("track", f"{saved_track['name']}")
    else:
      search_result = tidal.search("track", f"{saved_track['artists'][-1]} - {saved_track['name']}")
    found_tracks = [format_tidal_track(x) for x in search_result.tracks]
    
    tidal_id = None
    for found_track in found_tracks:
      log.debug(f"found result: {found_track}")
      if track_equal(found_track, saved_track, ignore_artists=ignore_artists_match):
        log.info(f"found equal track:\t{echo_track(found_track)}")
        tidal_id = found_track["tidal_id"]
        break

    # if not tidal_id:
    #   if not args.skip:
    #     print(f'equal track for {echo_track(saved_track)} not found')
    #     print(f'enter number to pick from below (-1 to ignore)')
    #     [print(f'{i} -> {echo_track(t)}') for i, t in enumerate(found_tracks)]
  
    # put found tidal_id to ignore in next processings
    saved_track["tidal_id"] = tidal_id
    db.data(key=saved_track_idx, value=saved_track)
    log.info(f'track {saved_track["name"]} updated with tidal_id = {saved_track["tidal_id"]}')
    
    sample_size -= 1
    if sample_size < 0:
      break

def print_non_founds(database_path):
  db = jsondb.Database(database_path)
  exported_tracks = {i: x for i, x in db.data().items() if not x.get("tidal_id") or x.get("tidal_id") == -1}
  exported_tracks_sorted = OrderedDict(sorted(exported_tracks.items(), key=lambda t: f'{", ".join(t[1].get("artists", []))} - {t[1].get("name", "")}'))
  log.warning(f'loaded: {len(exported_tracks_sorted.items())} "not-found" tracks')
  [print(f'{t["name"]:70}{", ".join(t.get("artists", [])):60}{t["album"]:40}') for i, t in exported_tracks_sorted.items()]

def manual_processing(database_path):
  db = jsondb.Database(database_path)
  # find only non-processed tracks
  exported_tracks = {i: x for i, x in db.data().items() if not x.get("tidal_id")}
  log.info(f'loaded: {len(exported_tracks.items())} "not-found" tracks')

  for saved_track_idx, saved_track in tqdm(exported_tracks.items(), unit=" track"):
    log.info(f"looking for track:\t{echo_track(saved_track)}")
    search_result = tidal.search("track", f"{saved_track['name']}")
    found_tracks = {i: format_tidal_track(x) for i, x in enumerate(search_result.tracks)}

    tidal_id = None
    if len(found_tracks) == 0:
      log.warning(f"NOTHING FOUND FOR {echo_track(saved_track)}")
    elif len(found_tracks) == 1:
      # somehow exact match found
      tidal_id = found_tracks[0]["tidal_id"]
    else:
      # manual select
      [print(f'{i}:\t{t["name"]:40}{", ".join(t.get("artists", [])):40}{t["album"]:40}') for i, t in found_tracks.items()]
      while tidal_id == None:
        selected_idx = int(input('ENTER number to pick from below (-1 to ignore): '))
        if selected_idx == -1:
          tidal_id = -1
        else:
          try:
            manually_selected_track = found_tracks.get(selected_idx, None)
            if manually_selected_track:
              tidal_id = manually_selected_track["tidal_id"]
              print(f'{echo_track(manually_selected_track)} with tidal_id = {tidal_id}')
          except Exception as e:
            log.exception(e)
      
    # update with picked
    if tidal_id != None:
      saved_track["tidal_id"] = tidal_id
      db.data(key=saved_track_idx, value=saved_track)
      log.info(f'track {saved_track["name"]} updated with tidal_id = {saved_track["tidal_id"]}')

def import_library(database_path, confirm=False, retry_count=5, sleep_timeout=5):
  db = jsondb.Database(database_path)
  tracks = db.data()
  tracks_to_skip = {}
  tracks_to_import = {}
  for idx, track in tracks.items():
    if not track.get("tidal_id", None) or track.get("tidal_id") == -1:
      tracks_to_skip[idx] = track
    else:
      tracks_to_import[idx] = track
  log.warning(f'you about to import\t{len(tracks_to_import.items())} tracks')
  log.warning(f'you about to skip\t{len(tracks_to_skip.items())} tracks')
  if not confirm:
    log.warning("supply flag --confirm true to execute import")
    exit(1)
  else:
    for idx, track in tqdm(tracks_to_import.items(), unit=" tracks"):

      local_retry_count = retry_count
      while local_retry_count >= 0:
        try:
          local_retry_count -= 1
          tidal.user.favorites.add_track(track["tidal_id"])
          track["exported_to_tidal"] = True
          break
        except Exception as e:
          # log.exception(e)
          log.exception(f'error during favorites.add_track -> {echo_track(track)}')
          time.sleep(sleep_timeout)
          track["exported_to_tidal"] = False
        
      db.data(key=idx, value=track)

      # print(track["name"])

if __name__ == "__main__":
  if args.first_processing:
    first_pricessing(args.load, args.find_only_by_track_name, args.process_not_founds, args.ignore_artists_match)
  if args.manual_processing:
    manual_processing(args.load)
  if args.print_non_founds:
    print_non_founds(args.load)
  if args.import_library:
    import_library(args.load, args.confirm)