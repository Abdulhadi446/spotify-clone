# Changelog

## v3.0 - Static Site (Current)

### Changed
- Removed all backend code (Cloudflare Worker, Python server, GitHub Actions)
- Removed download and new playlist functionality
- App is now fully static — just `index.html` + `songs.json` + MP3 files
- Simplified `loadLibrary()` to directly fetch `songs.json`

## v2.0 - Major Expansion

### Added Features
- Playlist/Folder support
- yt-dlp integration for downloads
- Metadata extraction from ID3 tags
- Media Session API integration
- Download modal dialog

## v1.0 - Initial Release

- Basic playback (play, pause, next, previous)
- Shuffle and repeat modes
- Volume control
- Progress bar with seeking
- Keyboard shortcuts
- Spotify-inspired UI
