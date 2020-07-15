# Spotify to Tidal Migration Toolset
This toolset will perform controlled import for your Spotify library (*i mean the liked songs*)

So nothing will be messed up (*mostly*)

For those who care (*like i am*)

## Requirements
- python3
- [just](https://github.com/casey/just#installation)
## Install
```bash
just install
```
## Configure
Put .env file in current directory with contents

**NOTE:** Spotify client creds could be obtained from [this instructions](https://spotipy.readthedocs.io/en/2.13.0/#getting-started)
```
SPOTIFY_CLIENT_ID=b53ccc1###
SPOTIFY_CLIENT_SECRET=d10e3###
TIDAL_LOGIN=your@email.com
TIDAL_PASSWORD=your_tidal_password
```
Then test it:
```bash
just spotify-export-test
```

## Usage
### Command list
```bash
$ just -l
Available recipes:
    install                      # intsall all python deps
    spotify-export               # perform spotify export with db save
    spotify-export-test          # test spotify export (is it really works?)
    tidal-clean                  # tidal favourites clean
    tidal-clean-confirm          # tidal favourites clean confirm
    tidal-first-processing       # find exact matches and set non-founds
    tidal-import-library         # import library to tidal
    tidal-import-library-confirm # confirm import
    tidal-manual-processing      # manually resolve non-founds
    tidal-second-processing      # second step of processing (find by track name + ignore match by artist)
    tidal-show-non-founds        # print what are not found
```

### Export Spotify library
```bash
just export
```

### Clean Tidal library
*Performance: ~100 tracks/minute*
```bash
just tidal-clean
```
And then
```bash
just tidal-clean-confirm
```

### Find exact matches between exported Spotify Library and Tidal
*Performance: ~80 tracks/minute*

Coverage: 90%
```bash
just tidal-first-processing
```

### Then find lazy matches (lookup only by track name then make match by album)
*Performance: ~80 tracks/minute*

*Coverage: 5%*
```bash
just tidal-first-processing
```

### Process the rest manually
**NOTE:** That really could take some time
```bash
just tidal-manual-processing
```

### Show the unfound rest
And then just **like** them in Tidal app otherwise **skip** it
```bash
just tidal-show-non-founds
```

### Import
*Performance: ~90 tracks/minute*
```bash
just tidal-import-library
```
And then
```bash
just tidal-import-library-confirm
```

## Enjoy your Music :tada:
Like you did that before (or never before)