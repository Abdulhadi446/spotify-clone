# Spotify Clone - Static Web Player

A beautiful, feature-rich Spotify clone built with vanilla HTML/CSS/JavaScript. Play local MP3s, organize them into playlists, download from YouTube/SoundCloud, and control playback with headphone buttons.

## Features

✨ **Playback**
- Play/pause, next/previous tracks
- Shuffle and repeat modes
- Progress bar with seek support
- Volume control
- Keyboard shortcuts (Space, Arrow keys, N, P)

🎧 **Media Session API**
- Headphone button support (play, pause, next, previous, seek)
- Lock screen / notification integration
- Position state tracking

📁 **Playlist Organization**
- Organize songs into folders (playlists)
- Collapsible playlist sections in sidebar
- Quick access to all songs

⬇️ **Download from URLs**
- Download songs from YouTube, SoundCloud, etc.
- Automatic metadata extraction (artist, title, album)
- Modal UI for easy downloading

🎵 **Smart Metadata**
- Automatic artist/title extraction from filenames
- Mutagen integration for ID3 tags
- Beautiful gradient thumbnails

## Installation

### Prerequisites
- Python 3.7+
- `mutagen`: `pip install mutagen`
- `yt-dlp`: `pip install yt-dlp`

### Setup

1. **Clone/setup the project:**
   ```bash
   cd spotify_clone
   ```

2. **Install Python dependencies:**
   ```bash
   pip install mutagen yt-dlp
   ```

3. **Start the server:**
   ```bash
   python3 server.py
   ```
   The server runs on `http://localhost:8080` by default.

4. **Open in browser:**
   - Open `index.html` directly OR
   - Navigate to `http://localhost:8080/` (recommended for downloads)

## Usage

### Playing Music

- Click any track in the list or sidebar to play
- Use play/pause button (Spacebar)
- Next/Previous buttons or arrow keys
- Progress bar for seeking

### Playlists

1. Add songs to folders in `media/` directory:
   ```
   media/
   ├── Favorites/
   │   ├── song1.mp3
   │   └── song2.mp3
   ├── Chill/
   │   └── song3.mp3
   └── song4.mp3 (root level songs)
   ```

2. Click the folder icon in sidebar to expand/collapse playlists
3. Click any song in a playlist to play

### Downloading Songs

1. Click the **+** button next to "Your Library" in the sidebar
2. Paste a YouTube or SoundCloud URL
3. Click "Download"
4. Song metadata is automatically extracted and added to your library
5. Page refreshes to show the new song

**Supported sources:**
- YouTube
- SoundCloud
- Instagram Reels
- TikTok
- And 500+ other sites (yt-dlp supports them all)

## Scripts

### Extract Metadata (`extract_meta.py`)

Scan the media directory and extract metadata from all MP3 files:

```bash
python3 extract_meta.py media/
```

Output: JSON with title, artist, album, duration for each file.

### Server (`server.py`)

HTTP server with APIs for downloads and playlist discovery:

```bash
python3 server.py [port]  # Default: 8080
```

**Endpoints:**
- `GET /api/tracks` - List all tracks with metadata
- `GET /api/playlists` - List playlists (folders)
- `POST /api/download` - Download song from URL
  ```json
  POST body: { "url": "https://..." }
  Response: { "title": "...", "artist": "...", "filename": "..." }
  ```

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

## API Configuration

By default, the app expects the server at `http://localhost:8080`. To change:

Edit `index.html` line ~1:
```javascript
const API_BASE = 'http://localhost:8080';
```

## File Structure

```
spotify_clone/
├── index.html           # Main player UI
├── server.py            # HTTP server with download/playlist APIs
├── extract_meta.py      # Metadata extraction utility
├── media/               # Your music files
│   ├── song1.mp3
│   ├── song2.mp3
│   ├── Favorites/       # Playlist folder
│   │   └── song3.mp3
│   └── Chill/           # Another playlist
│       └── song4.mp3
└── README.md           # This file
```

## Media Session API Support

When playing, headphone buttons work:
- **Play** - Resume playback
- **Pause** - Pause playback
- **Next** - Skip to next track
- **Previous** - Go to previous track
- **Seek Forward/Backward** - Jump ±10 seconds
- **Stop** - Stop and reset position

Lock screen and notifications show:
- Current track title
- Artist name
- Album/source
- Current playback position

## Troubleshooting

**Downloads not working?**
- Ensure server is running: `python3 server.py`
- Check API_BASE in `index.html` matches server URL
- Verify yt-dlp is installed: `pip install --upgrade yt-dlp`

**Metadata not extracting?**
- Install mutagen: `pip install mutagen`
- Check file format is valid MP3
- Run `python3 extract_meta.py media/` to debug

**Playlists not showing?**
- Create folders in `media/` directory
- Add MP3 files to the folders
- Refresh the page
- Check browser console for errors

**Keyboard shortcuts not working?**
- Ensure focus is NOT on an input field
- Check browser hasn't mapped the keys elsewhere

## License

This is a personal project. Feel free to use and modify!

## Credits

- **UI/UX**: Inspired by Spotify
- **Icons**: Material Design Icons
- **Metadata**: Mutagen library
- **Downloads**: yt-dlp
- **Playback Control**: Media Session API
