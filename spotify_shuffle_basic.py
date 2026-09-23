"""
Spotify Basic Shuffle
----------------------
Reads one of your Spotify playlists, shuffles it into a random order,
and creates a NEW playlist with that shuffled order.

Your original playlist is never modified.

Setup required before running:
1. pip install spotipy requests
2. Copy spotify_config.example.py to spotify_config.py and fill in your
   Client ID / Client Secret from https://developer.spotify.com/dashboard

Note: Spotify's February 2026 API update removed the old playlist-creation
and playlist-tracks endpoints. This script uses spotipy only for login,
and talks to Spotify's updated endpoints directly for everything else.
"""

import random
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import spotify_config as cfg

# Permissions needed: read playlists, and create/modify playlists
SCOPE = "playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public"

API_BASE = "https://api.spotify.com/v1"


def get_spotify_client():
    auth_manager = SpotifyOAuth(
        client_id=cfg.SPOTIPY_CLIENT_ID,
        client_secret=cfg.SPOTIPY_CLIENT_SECRET,
        redirect_uri=cfg.REDIRECT_URI,
        scope=SCOPE,
        cache_path=".spotify_token_cache",
        show_dialog=True,
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def get_access_token(sp):
    """Pull the raw bearer token out of spotipy so we can make direct
    requests to endpoints spotipy doesn't support yet."""
    token_info = sp.auth_manager.get_cached_token()
    return token_info["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def get_all_user_playlists(sp):
    playlists = []
    results = sp.current_user_playlists(limit=50)
    while results:
        playlists.extend(results["items"])
        if results["next"]:
            results = sp.next(results)
        else:
            results = None
    return playlists


def choose_playlist(playlists):
    usable = [pl for pl in playlists if pl]
    skipped = len(playlists) - len(usable)
    if skipped:
        print(f"(Skipped {skipped} playlist(s) Spotify returned as empty.)")

    print("\nYour playlists:")
    for i, pl in enumerate(usable):
        print(f"  [{i}] {pl.get('name', 'Untitled')}")

    while True:
        choice = input("\nEnter the number of the playlist to shuffle: ").strip()
        if choice.isdigit() and 0 <= int(choice) < len(usable):
            return usable[int(choice)]
        print("Invalid choice, try again.")


def get_all_tracks(token, playlist_id):
    """Fetch every track URI in the playlist using Spotify's current
    (post-Feb-2026) 'items' endpoint, handling pagination."""
    track_uris = []
    url = f"{API_BASE}/playlists/{playlist_id}/items"

    while url:
        response = requests.get(url, headers=auth_headers(token))
        response.raise_for_status()
        data = response.json()

        for entry in data.get("items", []):
            # Spotify renamed "track" to "item" in Feb 2026; check both
            # so this keeps working whichever key is present.
            track = entry.get("item") or entry.get("track")
            if track and track.get("uri"):
                track_uris.append(track["uri"])

        url = data.get("next")  # Spotify gives a full URL for the next page, or None

    return track_uris


def create_shuffled_playlist(token, original_name, shuffled_uris):
    new_name = f"{original_name} (Shuffled)"

    # Create the new (empty) playlist
    create_response = requests.post(
        f"{API_BASE}/me/playlists",
        headers=auth_headers(token),
        json={
            "name": new_name,
            "public": False,
            "description": f"Shuffled copy of '{original_name}'",
        },
    )
    create_response.raise_for_status()
    new_playlist_id = create_response.json()["id"]

    # Add tracks in batches of 100 (Spotify's per-call limit)
    batch_size = 100
    for i in range(0, len(shuffled_uris), batch_size):
        batch = shuffled_uris[i : i + batch_size]
        add_response = requests.post(
            f"{API_BASE}/playlists/{new_playlist_id}/items",
            headers=auth_headers(token),
            json={"uris": batch},
        )
        add_response.raise_for_status()

    return new_name


def main():
    sp = get_spotify_client()
    me = sp.current_user()
    token = get_access_token(sp)

    playlists = get_all_user_playlists(sp)
    if not playlists:
        print("No playlists found on this account.")
        return

    playlist = choose_playlist(playlists)
    print(f"\nFetching tracks from '{playlist['name']}'...")

    track_uris = get_all_tracks(token, playlist["id"])
    print(f"Found {len(track_uris)} tracks.")

    if not track_uris:
        print("No tracks found — nothing to shuffle.")
        return

    random.shuffle(track_uris)

    print("Creating shuffled playlist...")
    new_name = create_shuffled_playlist(token, playlist["name"], track_uris)

    print(f"\nDone! Created new playlist: '{new_name}'")
    print("Your original playlist was not modified.")


if __name__ == "__main__":
    main()
