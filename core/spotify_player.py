# Handles querying & playing songs.
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

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




def query_song_uri(query): # Find track with Whisper's output.
    result = sp.search(q=query, type="track", limit=1)
    if not result["tracks"]["items"]:
        print(f"No track was found for '{query}' [NEED TTS]")
        return None
    track = result["tracks"]["items"][0]
    print(track["name"], "-", track["artists"][0]["name"])
    print("Spotify URL:", track["external_urls"]["spotify"])
    print("URI:", track["uri"])
    return track["uri"]




def play_track(uri): # Play track via URI
    devices = sp.devices()
    if not devices["devices"]:
        print("No active Spotify devices detected [NEED TTS]")
        return
    device_id = devices["devices"][0]["id"]
    sp.start_playback(device_id=device_id, uris=[uri])

