# spotify_player.py — Handles querying & playing songs + AUTH
import os
import re
from dotenv import load_dotenv
from rapidfuzz import fuzz
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPE = "user-read-playback-state user-modify-playback-state user-read-currently-playing user-read-private"

# Spotify clients
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
))

sp_client = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
))


# ------------------- Search Helpers -------------------
def regular_query(query: str, max_tracks: int = 100, artist_name: str | None = None, artist_threshold: int = 40, query_name: str = "Regular Query"):
    """Search Spotify tracks with fuzzy scoring."""
    tracks = []
    offset = 0
    limit = 50

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
        return None, None, None, None, 0

    # Fuzzy matching
    best_match, best_score = None, 0
    query_lower = query.lower()
    for track in tracks:
        title_score = fuzz.token_set_ratio(query_lower, track["name"].lower())
        artist_score = 0
        if artist_name:
            artist_scores = [fuzz.token_set_ratio(artist_name.lower(), a["name"].lower()) for a in track["artists"]]
            artist_score = max(artist_scores)
            if artist_score < artist_threshold:
                continue
        combined_score = 0.7 * title_score + 0.3 * artist_score
        if combined_score > best_score:
            best_match = track
            best_score = combined_score

    if not best_match:
        return None, None, None, None, 0

    track_name = best_match["name"]
    artist_name_final = ", ".join([a["name"] for a in best_match["artists"]])
    uri = best_match["uri"]

    print(f"{query_name} Matched: {track_name} - {artist_name_final} | Score: {best_score}")
    print("Spotify URL:", best_match["external_urls"]["spotify"])
    return best_match, track_name, artist_name_final, uri, best_score


def simplify_title(title: str) -> str:
    """Remove '(feat. ...)' or '(with ...)' from titles."""
    return re.sub(r'\(feat[^\)]*\)|\(with[^\)]*\)', '', title, flags=re.IGNORECASE).strip()


def new_query(query: str, max_tracks: int = 100, artist_threshold: int = 40):
    """Artist-aware fuzzy search."""
    query_lower = query.lower()
    if " by " in query_lower:
        track_name, artist_name = map(str.strip, query_lower.split(" by ", 1))
    else:
        track_name, artist_name = query_lower, None
    return regular_query(track_name, max_tracks=max_tracks, artist_name=artist_name, artist_threshold=artist_threshold, query_name="New Query")


def query_best_song(query: str, max_tracks: int = 100, confidence_threshold: int = 94):
    """Return the best matching track based on fuzzy scoring."""
    new_track, new_name, new_artist, new_uri, new_score = new_query(query, max_tracks)
    if new_score >= confidence_threshold:
        print(f"Chosen Track (artist-aware): {new_name} - {new_artist} | Score: {new_score}")
        return new_track, new_name, new_artist, new_uri, new_score

    reg_track, reg_name, reg_artist, reg_uri, reg_score = regular_query(query, max_tracks)
    if reg_score >= confidence_threshold:
        print(f"Chosen Track (regular fallback): {reg_name} - {reg_artist} | Score: {reg_score}")
        return reg_track, reg_name, reg_artist, reg_uri, reg_score

    chosen = (new_track, new_name, new_artist, new_uri, new_score) if new_score >= reg_score else (reg_track, reg_name, reg_artist, reg_uri, reg_score)
    print(f"Choosing best available: {chosen[1]} - {chosen[2]} | Score: {chosen[4]}")
    return chosen


# ------------------- Playback Helpers -------------------
def get_track_info(track_id: str) -> dict | None:
    try:
        return sp_client.track(track_id)
    except Exception as e:
        print(f"Error fetching track info: {e}")
        return None


def get_artist_info(artist_id: str) -> dict | None:
    try:
        return sp_client.artist_related_artists(artist_id)
    except Exception as e:
        print(f"Error fetching artist info: {e}")
        return None


def play_track(uri: str, artist_uri: str | None = None):
    """Play a track and queue recommendations based on related artists."""
    devices = sp.devices().get("devices", [])
    if not devices:
        print("No active Spotify devices detected [NEED TTS]")
        return
    device_id = devices[0]["id"]

    sp.start_playback(device_id=device_id, uris=[uri])
    print(f"Now playing: {uri}")

    if artist_uri:
        queue_recommendations(uri, artist_uri=artist_uri, max_results=20)


def queue_recommendations(track_uri: str, artist_uri: str | None = None, max_results: int = 10):
    """Queue recommended tracks using related artists and their top tracks."""
    track_id = track_uri.split(":")[-1] if ":" in track_uri else track_uri.split("/")[-1]

    track_info = get_track_info(track_id)
    if not track_info:
        print(f"Cannot fetch track info for {track_id}")
        return []

    related_artist_ids = [a["id"] for artist in track_info["artists"] if (artist_info := get_artist_info(artist["id"])) for a in artist_info["artists"]]

    if artist_uri:
        artist_id = artist_uri.split(":")[-1] if ":" in artist_uri else artist_uri.split("/")[-1]
        if artist_id not in related_artist_ids:
            related_artist_ids.append(artist_id)

    if not related_artist_ids:
        print("No related artists found for recommendations.")
        return []

    recommended_tracks = []
    for artist_id in related_artist_ids:
        try:
            recommended_tracks.extend(sp_client.artist_top_tracks(artist_id).get("tracks", []))
        except Exception as e:
            print(f"Error fetching top tracks for artist {artist_id}: {e}")

    if not recommended_tracks:
        print("No recommended tracks found.")
        return []

    recommended_tracks = recommended_tracks[:max_results]

    devices = sp.devices().get("devices", [])
    if not devices:
        print("No active Spotify devices detected [NEED TTS]")
        return []

    device_id = devices[0]["id"]
    for t in recommended_tracks:
        try:
            sp.add_to_queue(t["uri"], device_id=device_id)
        except Exception as e:
            print(f"Error adding track {t['uri']} to queue: {e}")

    print(f"Queued {len(recommended_tracks)} recommended tracks based on {track_info['name']}")
    return recommended_tracks
