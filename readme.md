Pandora Station to Spotify
---------------

Play a Pandora station through Spotify, because Spotify radio stations are garbage.

## Getting

```
$ git clone --recursive git@github.com:synap5e/pandora-station-to-spotify.git
```

## Requirements

- Python 3
- [Requests](http://docs.python-requests.org/en/latest/) library

Expects Spotify to run a web-server for control on port 4370, which is default behavior for Spotify.

Runs on windows under cygwin or native Python. 
Should work on Linux if Spotify provides the same control server.

## Running

Set Pandora username and password in prefs.py.

```
$ python3 main.py
```

or

```
$ python3 main.py <station index>
```

Use `u`, `d`, `s` and `c` for thumbs up, thumbs down, skip, close respectively.
Thumbs down also skips.

## Caveats

Using the media controls within Spotify can result in unexpected behavior, as once the time has elapsed for a track a new track will be played.

## Future Work

Adding keyboard shortcuts.

Nicer station selection (argparse)

I would like to refactor the message passing and control, keeping the producer-consumer nature of the tracks, but making an extendable form of media control. This would allow more advanced actions (pause) and lead into some other form of interface (web, GUI app).

Adding ability to read the status back from Spotify to detect and respond to pauses and to shutdown/disable if a new song is selected in spotify. Possibly more full-featured Spotify integration.

> Pull requests welcome, although I have specific ideas for how the IPC should work. 
> If I like another solution more then I'll use it, otherwise maybe not.

## Submodules

Pandora Station to Spotify uses the following submodules:

- [My python3 fork](https://github.com/synap5e/spotify-local-http-api) of [cgbystrom/spotify-local-http-api](https://github.com/cgbystrom/spotify-local-http-api) for control of Spotify
- [pithos/pithos](https://github.com/pithos/pithos) for Pandora acess (GPLv3+)
- [joohoi's python3 fork](https://github.com/joohoi/spotipy) of [plamere/spotipy](https://github.com/plamere/spotipy) for access to the Spotify web API for finding songs (MIT)

## Licensing

MIT, but be aware when distributing the whole project that the GPLv3+ from pithos will apply.


