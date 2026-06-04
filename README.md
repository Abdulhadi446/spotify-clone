# Spotify Clone - Static Web Player

A beautiful, feature-rich Spotify clone built with vanilla HTML/CSS/JavaScript. Play local MP3s organized into playlists, with headphone button support via Media Session API.

## Features

- Play/pause, next/previous tracks
- Shuffle and repeat modes
- Progress bar with seek support
- Volume control
- Keyboard shortcuts (Space, Arrow keys, N, P)
- Media Session API (headphone button support, lock screen controls)
- Playlist organization via folders
- Smart metadata extraction from filenames
- Beautiful gradient thumbnails

## Usage

Simply open `index.html` in any browser, or serve the folder with any static file server:

```bash
python3 -m http.server 8080
```

### Playing Music

- Click any track to play
- Use play/pause button (Spacebar)
- Next/Previous buttons or arrow keys
- Progress bar for seeking

### Adding Music

1. Add MP3 files to folders in `media/` directory
2. Update `songs.json` with the track metadata
3. Refresh the page

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Play/Pause |
| ← | Rewind 10s |
| → | Forward 10s |
| ↑ | Volume up |
| ↓ | Volume down |
| N | Next track |
| P | Previous track |

## File Structure

```
spotify_clone/
├── index.html       # Main player UI
├── songs.json       # Track metadata catalog
├── media/           # MP3 files organized by playlist folders
│   ├── fav/         # Playlist with songs
│   └── ...          # More playlists
└── README.md        # This file
```

## Tech Stack

- Vanilla HTML + CSS + JavaScript (no frameworks)
- HTML5 `<audio>` element + Media Session API
- Google Fonts (DM Sans)
