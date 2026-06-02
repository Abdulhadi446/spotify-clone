# Changelog - Spotify Clone Updates

## v2.0 - Major Expansion (Current)

### Added Features

#### Core Functionality
- ✅ **Playlist/Folder Support** - Organize songs into folders that appear as collapsible playlists in sidebar
- ✅ **yt-dlp Integration** - Download songs directly from YouTube, SoundCloud, and 500+ other sites
- ✅ **Metadata Extraction** - Extract artist, title, album from ID3 tags or filenames
- ✅ **Media Session API** - Full headphone button support (play, pause, next, prev, seek)
- ✅ **HTTP Server** - Python server with API endpoints for downloads and playlist discovery

#### UI/UX Improvements
- ✅ Download modal dialog with URL input
- ✅ Real-time download status updates (loading, success, error)
- ✅ Collapsible playlist sections in sidebar
- ✅ Smooth animations for all interactions
- ✅ Better visual feedback for active/hover states
- ✅ Icon improvements (folder icons, status icons)

#### Developer Tools
- ✅ `server.py` - HTTP server with REST API
- ✅ `extract_meta.py` - Standalone metadata extraction utility
- ✅ `start.sh` - Quick start script
- ✅ Comprehensive documentation (README.md, IMPLEMENTATION.md)

### API Endpoints

```
GET  /api/tracks          - List all tracks with metadata
GET  /api/playlists       - List playlists (folders)
POST /api/download        - Download song from URL
```

### New JavaScript Functions

```javascript
openDownloadModal()              // Show download dialog
closeDownloadModal()             // Hide download dialog
downloadSong()                   // Process download
showStatus(type, msg)            // Show status messages
loadPlaylists()                  // Load playlists from server
renderSidebar()                  // Render playlist sections
togglePlaylist(name)             // Expand/collapse playlist
playPlaylistTrack(pl, file)      // Play song from playlist
```

### New CSS Classes

```css
.modal                    /* Modal dialog container */
.modal.active             /* Show modal */
.modal-content            /* Modal dialog box */
.modal-header             /* Title + close button */
.input-group              /* Form group styling */
.btn-primary              /* Primary action button */
.status-message           /* Status display */
.status-message.success   /* Success state */
.status-message.error     /* Error state */
.status-message.loading   /* Loading state */
.playlist-folder          /* Folder/playlist container */
.playlist-folder-header   /* Folder header (clickable) */
.playlist-folder-toggle   /* Expand/collapse indicator */
.playlist-folder-content  /* Folder contents */
.playlist-folder-content.expanded /* Expanded folder */
```

### File Structure Changes

**New Files:**
- `server.py` - HTTP server (250 lines)
- `extract_meta.py` - Metadata utility (130 lines)
- `start.sh` - Quick start script (35 lines)
- `README.md` - Full documentation
- `IMPLEMENTATION.md` - Implementation details
- `CHANGELOG.md` - This file

**Updated Files:**
- `index.html` - Full rebuild with new features (+500 lines)

**New Directories:**
- `media/Favorites/` - Example playlist
- `media/Chill/` - Example playlist
- `media/Vibes/` - Example playlist
- `media/Punjabi/` - Example playlist

### Dependencies Added

**Python:**
- `mutagen>=1.45.0` - MP3 metadata extraction
- `yt-dlp>=2023.0.0` - Download from URL

**Browser:**
- None! Still vanilla JavaScript

### Improvements to Existing Features

#### Media Session API
- Now properly updates position state on every time update
- Better error handling for browsers without full support
- All 6 button actions implemented

#### Metadata Parsing
- Improved regex for multiple separators (-, –, |, ｜)
- Better handling of featured artists
- Smarter title cleaning (removes common patterns)
- Fallback chain: ID3 tags → filename regex → defaults

#### Sidebar
- Converted to flex layout for better scrolling
- Separate rendering for playlists vs. tracks
- Smooth expand/collapse animations
- Shows song counts for playlists

### Bug Fixes

- Fixed media session state sync issues
- Improved keyboard shortcut handling
- Better error handling in API calls
- Proper CORS headers on all responses
- Fixed scrollbar styling for playlists

### Performance

- No change in bundle size for HTML (still under 50KB)
- Server is lightweight (~300 lines Python)
- Metadata extraction is O(n) - scans once at startup
- Playlist rendering is efficient even with 1000+ songs

### Breaking Changes

None - fully backward compatible with v1.0

### Known Limitations

1. **Server Required for Downloads** - Headless operation possible but downloads won't work
2. **File System Limits** - Tested with up to 1000 songs
3. **Playlist Sync** - Playlists are read-only (file system organized)
4. **Storage** - All data stored locally (no cloud sync)
5. **Browser Support** - Media Session API not on all browsers

## v1.0 - Initial Release

### Original Features
- ✅ Basic playback (play, pause, next, previous)
- ✅ Shuffle and repeat modes
- ✅ Volume control
- ✅ Progress bar with seeking
- ✅ Keyboard shortcuts
- ✅ Track list display
- ✅ Basic Media Session API support
- ✅ Beautiful Spotify-inspired UI
- ✅ Gradient thumbnails for tracks

---

**Total Lines Added:** ~1500 (Python scripts + HTML/CSS/JS)
**Total Files:** 10 (including docs)
**Compatibility:** Fully backward compatible
**Breaking Changes:** None
