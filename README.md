# Spotify Clone

A music player with two interfaces — **static web** (HTML/JS) and **desktop app** (Python/customtkinter).

## Desktop App

```bash
# setup
python3 -m venv .venv
source .venv/bin/activate
pip install customtkinter pygame

# run
python3 spotify_player.py
```

## Web App

Open `index.html` in any browser.

## Add a Song

```bash
python3 add_song.py "https://youtube.com/watch?v=..." [playlist]
```

Downloads audio, updates `songs.json`, commits and pushes to GitHub.

## File Structure

```
spotify_clone/
├── index.html           # Web player
├── spotify_player.py    # Desktop player
├── add_song.py          # Download + add tool
├── songs.json           # Track metadata
├── media/               # MP3 files by playlist folder
└── README.md
```
