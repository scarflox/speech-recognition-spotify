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


def regular_query(query, max_tracks=200):
    tracks = []
    offset = 0
    limit = 50  # max allowed per Spotify search request

    while len(tracks) < max_tracks:
        result = sp.search(q=query, type="track", limit=limit, offset=offset)
        items = result.get("tracks", {}).get("items", [])
        if not items:
            break
        tracks.extend(items)
        if len(items) < limit:
            break
        offset += limit

    if not tracks:
        print(f"No track was found for '{query}' [NEED TTS]")
        return None, None, None, None, 0

    # Pick the first track as best match
    track = tracks[0]
    track_name_final = track["name"]
    artist_name_final = ", ".join([a["name"] for a in track["artists"]])
    uri = track["uri"]
    score = 100  # assume 100% confidence for first search result

    print(f"{track_name_final} - {artist_name_final}")
    print("Regular Search Spotify URL:", track["external_urls"]["spotify"])
    print("Regular Search URI:", uri)

    return track, track_name_final, artist_name_final, uri, score



def new_query(query, max_tracks=200, artist_threshold=40):
    tracks = []
    offset = 0
    limit = 50  # Spotify max per request

    # -----------------------
    # Parse transcription (normalize once)
    # -----------------------
    query_lower = query.lower()

    if " by " in query_lower:
        parts = query_lower.split(" by ")
        track_name = parts[0].strip()
        artist_name = parts[1].strip()
    else:
        track_name = query_lower.strip()
        artist_name = None

    # -----------------------
    # Fetch tracks via pagination
    # -----------------------
    while len(tracks) < max_tracks:
        result = sp.search(q=track_name, type="track", limit=limit, offset=offset)
        items = result.get("tracks", {}).get("items", [])
        if not items:
            break
        tracks.extend(items)
        if len(items) < limit:
            break
        offset += limit

    if not tracks:
        print(f"No track found for '{query}' [NEED TTS]")
        return None, None, None, None, 0

    # -----------------------
    # Compute weighted fuzzy scores with artist threshold
    # -----------------------
    best_match = None
    best_score = 0

    for track in tracks:
        title_score = fuzz.token_set_ratio(track_name, track["name"].lower())
        artist_score = 0

        if artist_name:
            artist_scores = [
                fuzz.token_set_ratio(artist_name, a["name"].lower())
                for a in track["artists"]
            ]
            artist_score = max(artist_scores)

            # Skip tracks with artist too dissimilar
            if artist_score < artist_threshold:
                continue

        combined_score = 0.7 * artist_score + 0.3 * title_score
        if combined_score > best_score:
            best_score = combined_score
            best_match = track

    # -----------------------
    # Fallback search if nothing passes threshold
    # -----------------------
    if not best_match:
        fallback = sp.search(q=query_lower, type="track", limit=10)
        fallback_items = fallback.get("tracks", {}).get("items", [])
        fallback_best = None
        fallback_score = 0

        for track in fallback_items:
            title_score = fuzz.token_set_ratio(track_name, track["name"].lower())
            artist_score = 0

            if artist_name:
                artist_scores = [
                    fuzz.token_set_ratio(artist_name, a["name"].lower())
                    for a in track["artists"]
                ]
                artist_score = max(artist_scores)
                if artist_score < artist_threshold:
                    continue

            combined_score = 0.7 * artist_score + 0.3 * title_score
            if combined_score > fallback_score:
                fallback_score = combined_score
                fallback_best = track

        best_match = fallback_best
        best_score = fallback_score

    # -----------------------
    # Return result
    # -----------------------
    if not best_match:
        return None, None, None, None, 0

    track_name_final = best_match["name"]
    artist_name_final = ", ".join([a["name"] for a in best_match["artists"]])
    uri = best_match["uri"]

    print(f"Matched track: {track_name_final} - {artist_name_final} | Score: {best_score}%")
    print("Spotify URL:", best_match["external_urls"]["spotify"])
    return best_match, track_name_final, artist_name_final, uri, best_score

def query_best_song(query, max_tracks=500, confidence_threshold=50):
    transcription_lower = query.lower()

    # 1️⃣ Run artist-aware + fuzzy search
    new_track, new_name, new_artist, new_uri, new_score = new_query(query, max_tracks=max_tracks)
    new_title_score = fuzz.token_set_ratio(transcription_lower, new_name.lower()) if new_name else 0

    # Short-circuit if 100% title match
    if new_title_score == 100:
        return new_track, new_name, new_artist, new_uri, new_score

    # 2️⃣ Run global fallback search
    reg_track, reg_name, reg_artist, reg_uri, reg_score = regular_query(query, max_tracks=max_tracks)
    reg_title_score = fuzz.token_set_ratio(transcription_lower, reg_name.lower()) if reg_name else 0

    if reg_title_score == 100:
        return reg_track, reg_name, reg_artist, reg_uri, reg_score

    # 3️⃣ Compute combined score for tie-breaking
    new_artist_score = fuzz.token_set_ratio(transcription_lower, new_artist.lower()) if new_artist else 0
    reg_artist_score = fuzz.token_set_ratio(transcription_lower, reg_artist.lower()) if reg_artist else 0

    new_combined = 0.7 * new_title_score + 0.3 * new_artist_score
    reg_combined = 0.7 * reg_title_score + 0.3 * reg_artist_score

    # 4️⃣ Pick the best
    if new_combined >= reg_combined:
        chosen = new_track
        chosen_name = new_name
        chosen_artist = new_artist
        chosen_uri = new_uri
        chosen_score = new_combined
    else:
        chosen = reg_track
        chosen_name = reg_name
        chosen_artist = reg_artist
        chosen_uri = reg_uri
        chosen_score = reg_combined

    print(f"Chosen track: {chosen_name} - {chosen_artist} | Combined score: {chosen_score}")
    return chosen, chosen_name, chosen_artist, chosen_uri, chosen_score

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

