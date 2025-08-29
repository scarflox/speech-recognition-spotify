# Handles querying & playing songs.
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
from rapidfuzz import process, fuzz

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8888/callback"

scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=REDIRECT_URI,
    scope=scope
))


def regular_query(query, return_details=False, max_tracks=500):
    tracks = []
    offset = 0
    limit = 50  # max allowed per Spotify search request

    while len(tracks) < max_tracks:
        result = sp.search(q=query, type="track", limit=limit, offset=offset)
        items = result.get("tracks", {}).get("items", [])
        if not items:
            break  # no more results
        tracks.extend(items)
        if len(items) < limit:
            break  # last page
        offset += limit

    if not tracks:
        print(f"No track was found for '{query}' [NEED TTS]")
        return (None, None, None) if return_details else None

    # Pick the first track as “best match”
    track = tracks[0]
    print(track["name"], "-", track["artists"][0]["name"])
    print("Regular Search Spotify URL:", track["external_urls"]["spotify"])
    print("Regular Search URI:", track["uri"])
    if return_details:
        return track["uri"], track["name"], track["artists"][0]["name"]
    return track["uri"]


def query_song_uri(query, return_details=False, max_tracks=500):
    """
    Find best match for a query using an artist-specific search.
    Fetches up to `max_tracks` from the artist instead of just top tracks.
    """

    if " by " in query.lower():
        parts = query.lower().split(" by ")
        track_name = parts[0].strip()
        artist_name = parts[1].strip()

        # Search for artist
        artist_query = sp.search(q=f'artist:"{artist_name}"', type="artist", limit=1)
        if not artist_query or not artist_query["artists"]["items"]:
            print(f"No artist found for '{artist_name}', falling back to regular query.")
            return regular_query(query, return_details=return_details)

        artist_id = artist_query["artists"]["items"][0]["id"]

        # Fetch artist albums and singles (paginated)
        albums = []
        offset = 0
        while len(albums) < max_tracks:
            batch = sp.artist_albums(
                artist_id,
                album_type='album,single,compilation',
                limit=50,
                offset=offset
            )["items"]
            if not batch:
                break
            albums.extend(batch)
            if len(batch) < 50:
                break
            offset += 50

        # Collect tracks from albums
        artist_tracks = []
        for album in albums:
            album_tracks = sp.album_tracks(album['id'])['items']
            for t in album_tracks:
                artist_tracks.append(t)
                if len(artist_tracks) >= max_tracks:
                    break
            if len(artist_tracks) >= max_tracks:
                break

        if not artist_tracks:
            print(f"No tracks found for artist '{artist_name}', falling back to regular query.")
            return regular_query(query, return_details=return_details)

        # Fuzzy match the transcription to track names
        track_names = [t["name"] for t in artist_tracks]
        result = process.extractOne(track_name, track_names, scorer=fuzz.token_sort_ratio)

        if result is None:
            print("No matching track found in artist tracks, falling back to global search.")
            return regular_query(query, return_details=return_details)

        best_match, score, _ = result
        matched_track = next((t for t in artist_tracks if t["name"].lower() == best_match.lower()), None)

        if not matched_track:
            print("Could not resolve fuzzy match to a track object, falling back to global search.")
            return regular_query(query, return_details=return_details)

        print(f"Matched track: {matched_track['name']} - {matched_track['artists'][0]['name']}")
        print("Artist query Spotify URL:", matched_track["external_urls"]["spotify"])
        print("Artist query URI:", matched_track["uri"])

        if return_details:
            return matched_track["uri"], matched_track["name"], matched_track["artists"][0]["name"]
        return matched_track["uri"]

    else:
        # No artist specified → fallback to regular query
        print("No artist specified in query, running regular search.")
        return regular_query(query, return_details=return_details)


def query_best_song(query):
    print("Running regular query")
    regular_uri, regular_name, regular_artist = regular_query(query, return_details=True)

    print("Running fuzzy artist-top-tracks query...")
    fuzzy_uri, fuzzy_name, fuzzy_artist = query_song_uri(query, return_details=True)

    if not regular_uri and not fuzzy_uri:
        print("No track was found in any query. [DEBUG]")
        return None
    
    if regular_uri and not fuzzy_uri:
        return regular_uri
    if fuzzy_uri and not regular_uri:
        return fuzzy_uri
    
    # In case both queries exist, we must find the best result compared to our transcription.

    regular_score = fuzz.token_sort_ratio(query.lower(), f"{regular_name} {regular_artist}".lower())
    fuzzy_score = fuzz.token_sort_ratio(query.lower(), f"{fuzzy_name} {fuzzy_artist}".lower())

    print(f"Similarity scores: Regular - {regular_score}, Fuzzy - {fuzzy_score}")
    if fuzzy_score >= regular_score:
        print(f"Chosen track (regular): {fuzzy_name} - {fuzzy_artist}")
        return fuzzy_uri
    else:
        print(f"Chosen track (regular): {regular_name} - {regular_artist}")
        return regular_uri


def play_track(uri): # Play track via URI
    devices = sp.devices()
    if devices is None:
        print("No device was found [NEED TTS]")
        return
    
    if not devices["devices"]:
        print("No active Spotify devices detected [NEED TTS]")
        return
    device_id = devices["devices"][0]["id"]
    sp.start_playback(device_id=device_id, uris=[uri])

