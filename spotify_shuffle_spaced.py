"""
Spotify Spaced Shuffle
------------------------
Same as the basic shuffle script, but tries to avoid playing the same
artist again too soon. Uses each track's main (first-listed) artist.

Reads one of your Spotify playlists, shuffles it so that the same artist
doesn't appear again within MIN_ARTIST_GAP tracks (when possible), and
creates a NEW playlist with that order.

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

# Minimum number of tracks that must pass before the same artist can repeat.
# Set to 0 to disable spacing (same as the basic shuffle).
MIN_ARTIST_GAP = 5


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


def get_all_tracks_with_artist(token, playlist_id):
    """Fetch every track's URI plus its main (first-listed) artist name,
    using Spotify's current (post-Feb-2026) 'items' endpoint."""
    tracks = []
    url = f"{API_BASE}/playlists/{playlist_id}/items"

    while url:
        response = requests.get(url, headers=auth_headers(token))
        response.raise_for_status()
        data = response.json()

        for entry in data.get("items", []):
            # Spotify renamed "track" to "item" in Feb 2026; check both
            # so this keeps working whichever key is present.
            track = entry.get("item") or entry.get("track")
            if track and track.get("uri") and track.get("artists"):
                tracks.append(
                    {
                        "uri": track["uri"],
                        "name": track.get("name", "Unknown"),
                        "artist": track["artists"][0]["name"],
                    }
                )

        url = data.get("next")

    return tracks


def spaced_shuffle(tracks, min_gap):
    """
    Shuffle tracks so the same main artist doesn't repeat within `min_gap`
    tracks, when possible. Falls back to placing a track anyway if no
    valid spot exists (e.g. one artist dominates the playlist), so no
    tracks are ever dropped.
    """
    remaining = tracks[:]
    random.shuffle(remaining)

    result = []
    problems = 0

    while remaining:
        placed = False
        recent_artists = {t["artist"] for t in result[-min_gap:]} if min_gap > 0 else set()

        random.shuffle(remaining)
        for i, candidate in enumerate(remaining):
            if candidate["artist"] not in recent_artists:
                result.append(remaining.pop(i))
                placed = True
                break

        if not placed:
            result.append(remaining.pop(0))
            problems += 1

    return result, problems


def create_shuffled_playlist(token, original_name, shuffled_tracks):
    new_name = f"{original_name} (Spaced Shuffle)"

    create_response = requests.post(
        f"{API_BASE}/me/playlists",
        headers=auth_headers(token),
        json={
            "name": new_name,
            "public": False,
            "description": f"Spaced shuffle copy of '{original_name}' (min artist gap: {MIN_ARTIST_GAP})",
        },
    )
    create_response.raise_for_status()
    new_playlist_id = create_response.json()["id"]

    uris = [t["uri"] for t in shuffled_tracks]

    batch_size = 100
    for i in range(0, len(uris), batch_size):
        batch = uris[i : i + batch_size]
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

    tracks = get_all_tracks_with_artist(token, playlist["id"])
    print(f"Found {len(tracks)} tracks.")

    if not tracks:
        print("No tracks found — nothing to shuffle.")
        return

    print(f"Shuffling with minimum artist gap of {MIN_ARTIST_GAP}...")
    shuffled, problems = spaced_shuffle(tracks, MIN_ARTIST_GAP)

    if problems:
        print(f"Note: {problems} track(s) couldn't fully satisfy the artist gap "
              f"(this happens if one artist has a lot of tracks).")
    else:
        print("Spacing worked perfectly — no artist gap problems.")

    print("Creating shuffled playlist...")
    new_name = create_shuffled_playlist(token, playlist["name"], shuffled)

    print(f"\nDone! Created new playlist: '{new_name}'")
    print("Your original playlist was not modified.")


if __name__ == "__main__":
    main()
