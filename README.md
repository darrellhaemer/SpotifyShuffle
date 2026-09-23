# Spotify Shuffle Scripts

Two small Python scripts that give you a **shuffle that never repeats a song** until the whole playlist has played.

Spotify's built-in shuffle can repeat songs and clump things together. These scripts work around that: they read one of your playlists, put the tracks in a random order, and save the result as a **new playlist**. You turn Spotify's shuffle *off* and play the new playlist from the top. Every track plays exactly once.

- **`spotify_shuffle_basic.py`** makes a plain random shuffle, named `Your Playlist (Shuffled)`.
- **`spotify_shuffle_spaced.py`** makes a random shuffle that also keeps the same main artist from coming up again within a set number of tracks (default 5), named `Your Playlist (Spaced Shuffle)`.

**Your original playlist is never changed.** The scripts only read from it and create a new playlist.


## Please read first

- **This is unofficial.** It is not made, endorsed, or supported by Spotify. It uses the official Spotify API, but Spotify could change things and break it. I can't guarantee it will keep working, and you use it at your own risk. Check Spotify's terms of service if you're unsure.

## IMPORTANT - PLEASE READ
- **Never share `.spotify_token_cache`.** The first time you run a script, it saves a file called `.spotify_token_cache` next to it. That file works like a saved login to your Spotify account. DON'T UPDLOAD IT, EMAIL IT, OR INCLUDE IT IN A ZIP. If it ever gets out, change your Spotify password and sign out your other sessions.
- **Your password is never handled by the script.** You log in on Spotify's own website, and the script only receives the resulting login token.
- **Tested only on Windows**, with Python 3.14. Other recent versions of Python 3 will likely work, and Mac/Linux probably work too, but I haven't tested them.


## Setup

### 1. Install Python

Download Python from the official site, **https://www.python.org/downloads/**, and run the installer. Only download it from python.org.

On Windows, the installer may offer to add Python to your PATH. Say **yes** (`y`, or tick the "Add python.exe to PATH" checkbox). If it asks whether to install Python (CPython) now, say **yes**.

Then **close any open PowerShell or Terminal window and open a new one (press the Windows key, type Powershell, press Enter)**, and check that it worked by entering:
```
python --version
```

You should see a version number. If Windows says `python` isn't recognized, try `py --version`, and use `py` instead of `python` for the rest of these steps. On Mac/Linux you may need `python3` instead of `python`.


### 2. Install the required libraries:

In Powershell, enter:
Note: "spotipy" is not a typo.
```
pip install spotipy requests
```


### 3. Create a Spotify Developer account and register an app

Spotify doesn't make this easy for us. Unfortunately, every user of this script has to be a registered Spotify Developer. It's not hard to do, just annoying.

1. Go to 'https://developer.spotify.com/dashboard' and log in with your normal Spotify account.

2. Click Create app. Fill in any name/description (e.g. "Personal Shuffle Tool"). Choose "Web API".

3. For Redirect URI, enter exactly: 'http://127.0.0.1:8888/callback' — this needs to match what's in the script later, so keep it exact.

4. You will need your Client ID and Client Secret, so keep these handy for a minute.


### 4. Get the scripts

Download `spotify_shuffle_basic.py` and `spotify_shuffle_spaced.py` and put them in a folder.


## Using it

1. You should be able to double-click either spotify_shuffle_basic.py or spotify_shuffle_spaced.py to run it. If that works, skip down to step 2. If double-clicking doesn't work, try the following:

A. Open PowerShell (or Terminal) and navigate to your folder with something like:
   ```
   cd C:\SpotifyShuffle
   ```
B. Run one of the scripts by entering either of the following:
   ```
   python spotify_shuffle_basic.py
   python spotify_shuffle_spaced.py
   ```

2. **First run only:** the script prints a link. Open it in your browser and approve the login with your Spotify account. The script then continues on its own.
3. Type the number of the playlist you want to duplicate and shuffle and press Enter.
4. Wait a few seconds. When it says it's done, find the new playlist in Spotify.
5. In Spotify, turn **shuffle off**, make sure the playlist is sorted by **Date Added** (that column holds the shuffled order), and press play on the first track.

Each script run creates a new playlist. Delete old shuffled copies by hand when you're done with them.


## Settings

In `spotify_shuffle_spaced.py`, near the top of the file:

```python
MIN_ARTIST_GAP = 5
```

This is the minimum number of *other* tracks between two songs by the same main artist. Only the main artist counts (featured artists are ignored). If a playlist is dominated by one artist, the gap can't always be met, and the script spaces them as far apart as it can. It prints how many tracks couldn't meet the gap before it creates the playlist.

## Troubleshooting

- **Login fails or keeps failing.** Delete `.spotify_token_cache` from the script's folder and run again.
- **The copy has fewer tracks than the original.** Some tracks may be unavailable in your region or may have been removed from Spotify.
- **It stopped partway through.** Delete the incomplete playlist in Spotify and run again. Your original is unaffected.
- **It used to work and now doesn't.** Spotify's API may have changed. Open an issue with the full error message.

## Disclaimer

Not affiliated with Spotify. Spotify is a trademark of its owner. This software is provided as is, without warranty of any kind. See the LICENSE file.
