disliked_words = ['live', 'remix', 'mix']

import sys, os, time, string, queue

if sys.version_info[0] != 3:
    print('Requires Python 3')
    exit()

import prefs

from collections import namedtuple
RATE_BAN = 'ban'
RATE_LOVE = 'love'
RATE_NONE = None
Feedback = namedtuple('Feedback', ['rating', 'token'])

def strip_non_ascii(string):
    ''' Returns the string without non ASCII characters'''
    # http://stackoverflow.com/a/2743163
    stripped = (c for c in string if 0 < ord(c) < 127)
    return ''.join(stripped)

def pandora_2_spotify(spotify_api, pandora_track):
    q = 'track:"{songname}" artist:"{artist}"'.format(
        songname = pandora_track.songName,
        artist   = pandora_track.artist
    )

    search = spotify_api.search(q)
    tracks = search['tracks']['items']

    if not tracks:
        return None

    preferred_tracks = []
    for track in tracks:
        name = track['name'].lower()
        bad = False
        for w in disliked_words:
            if w in name:
                bad = True
            if ('(%s)' % bad) in name:
                bad = True
        if not bad:
            preferred_tracks.append(track)

    if not preferred_tracks:
        preferred_tracks = tracks

    track = tracks[0]
    
    return track



def feed_songs(songs, stop_event, feedback_queue, station=1):
    # import pandora control from pithos
    sys.path.append(os.getcwd() + '/submodules/pithos/pithos/')
    import pandora, pandora.data

    pandora_client = pandora.Pandora()

    client = pandora.data.client_keys[pandora.data.default_client_id]
    pandora_client.connect(client, prefs.username, prefs.password)
    pandora_client.set_audio_quality('lowQuality')

    # import spotify web api library
    sys.path.append(os.getcwd() + '/submodules/spotipy/')
    import spotipy



    sp = spotipy.Spotify()

    current_station = pandora_client.get_stations()[station]
    print('\n~~~~ Playing from station "%s" ~~~~\n' % current_station.name)

    while not stop_event.is_set():
        while True:
            try:
                feedback = feedback_queue.get_nowait()
                print ('^^ Adding feedback')
                pandora_client.add_feedback(feedback.token, feedback.rating)
            except queue.Empty:
                break
        print('-- Fetching next playlist -- ')
        playlist = current_station.get_playlist()
        for pandora_track in playlist:
            spotify_track = pandora_2_spotify(sp, pandora_track)
            if spotify_track:
                songs.put((spotify_track, pandora_track.trackToken))
                print ('<< Adding "%s" (%d)' % (strip_non_ascii(spotify_track['name']), songs.qsize()))

def play_songs(songs, stop_event, skip_event, current_song, plays='plays.txt'):
    if plays:
        plays_file = open(plays, 'a+')

    # import spotify remote 
    sys.path.append(os.getcwd() + '/submodules/spotify-local-http-api/')
    import http_remote as spotify_remote

    oauth_token = spotify_remote.get_oauth_token()
    csrf_token = spotify_remote.get_csrf_token()

    def play_spotify_uri(spotify_uri):
        return 'error' not in spotify_remote.play(oauth_token, csrf_token, spotify_uri)

    while not stop_event.is_set():
        print('>> ', end='')
        track, pandora_token = songs.get()
        print ('Playing "%s"' % (strip_non_ascii(track['name'])))
        duration_ms = track['duration_ms']
        uri = track['uri']
        skip_event.clear()
        if play_spotify_uri(uri):
            current_song['pandora_token'] = pandora_token
            current_song['title'] = track['name']
            #current_song['artist'] = track['artist']
            current_song['uri'] = uri

            if plays:
                plays_file.write(uri + '\n')
                plays_file.flush()

            duration_ms += 100
            skip_event.wait(duration_ms/1000.0)
    if plays:
        plays_file.close()

    # Eat all remaining songs. Not a perfect solution and can fail to stop the feeder in a race condition
    while True:
        try:
            songs.get_nowait()
        except queue.Empty:
            break


def cli_interface(fileno, stop_event, skip_event, feedback, current_song, ups='ups.txt'):
    if ups:
        ups_file = open(ups, 'a+')

    sys.stdin.close()
    sys.stdin = open(fileno)
    def up():
        print('** thumbs up')
        if ups:
            ups_file.write(current_song['uri'] + '\n')
            ups_file.flush()
        feedback.put(Feedback(rating=RATE_LOVE, token=current_song['pandora_token']))
    def down():
        print('** thumbs down')
        feedback.put(Feedback(rating=RATE_BAN, token=current_song['pandora_token']))
        skip_event.set()
    def skip():
        print('** skip')
        skip_event.set()
    def close():
        print('** close')
        stop_event.set()
        skip_event.set()
    commands = [
        up, down, skip, close
    ]
    while not stop_event.is_set():
        print('commands: [u]p, [d]own, [s]kip, [c]lose')
        command = input().lower()
        if command:
            for c in commands:
                if c.__name__.startswith(command):
                    c()
                    break
    if ups:
        ups_file.close()


if __name__ == '__main__':
    station = 1
    if len(sys.argv) > 1:
        station = int(sys.argv[1])

    import multiprocessing
    
    manager = multiprocessing.Manager()

    songs        = multiprocessing.Queue(maxsize=prefs.queue_size) 
    
    stop_event   = multiprocessing.Event()
    skip_event   = multiprocessing.Event()
    feedback     = multiprocessing.Queue()
    current_song = manager.dict()

    feeder       = multiprocessing.Process(target=feed_songs,    args=(songs, stop_event, feedback), kwargs={'station' : station})
    player       = multiprocessing.Process(target=play_songs,    args=(songs, stop_event, skip_event, current_song))
    interface    = multiprocessing.Process(target=cli_interface, args=(sys.stdin.fileno(), stop_event, skip_event, feedback, current_song))

    sys.stdin.close()

    feeder.start()
    player.start()
    interface.start()

    feeder.join()
    player.join()
    interface.join()

