buffer_file := "spotify-export.txt"

### SETUP
# intsall all python deps
install:
  pip3 install -r requirements.txt

### SPOTIFY ACTIONS
# test spotify export (is it really works?)
spotify-export-test:
  python3 spotify-export.py $SPOTIFY_CLIENT_ID $SPOTIFY_CLIENT_SECRET
# perform spotify export with db save
spotify-export:
  python3 spotify-export.py $SPOTIFY_CLIENT_ID $SPOTIFY_CLIENT_SECRET --save {{buffer_file}}

### TIDAL ACTIONS
# find exact matches and set non-founds
tidal-first-processing:
  python3 import-tidal.py $TIDAL_LOGIN $TIDAL_PASSWORD --load {{buffer_file}} --debug true --first_processing true
# second step of processing (find by track name + ignore match by artist)
tidal-second-processing:
  python3 import-tidal.py $TIDAL_LOGIN $TIDAL_PASSWORD --load {{buffer_file}} --debug true --first_processing true --find_only_by_track_name true --process_not_founds true --ignore_artists_match true
# manually resolve non-founds
tidal-manual-processing:
  python3 import-tidal.py $TIDAL_LOGIN $TIDAL_PASSWORD --load {{buffer_file}} --debug true --manual_processing true
# print what are not found
tidal-show-non-founds:
  python3 import-tidal.py $TIDAL_LOGIN $TIDAL_PASSWORD --load {{buffer_file}} --print_non_founds true
# import library to tidal
tidal-import-library:
  python3 import-tidal.py $TIDAL_LOGIN $TIDAL_PASSWORD --load {{buffer_file}} --debug true --import_library true
# confirm import
tidal-import-library-confirm:
  python3 import-tidal.py $TIDAL_LOGIN $TIDAL_PASSWORD --load {{buffer_file}} --debug true --import_library true --confirm true

### TIDAL CLEAN
# tidal favourites clean
tidal-clean:
  python3 import-tidal.py $TIDAL_LOGIN $TIDAL_PASSWORD --clean true
# tidal favourites clean confirm
tidal-clean-confirm:
  python3 import-tidal.py $TIDAL_LOGIN $TIDAL_PASSWORD --clean true --confirm true