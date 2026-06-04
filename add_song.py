#!/usr/bin/env python3
"""Download a song from YouTube and add it to the playlist."""

import argparse, json, os, re, shutil, subprocess, sys, tempfile

SONGS_JSON = "songs.json"
MEDIA_DIR = "media"


def clean_title(title: str) -> str:
    title = re.sub(r"\s*\(Official\s*(Lyric\s*)?Video\)\s*", "", title, flags=re.I)
    title = re.sub(r"\s*\(Official\s*Audio\)\s*", "", title, flags=re.I)
    title = re.sub(r"\s*\(Lyrics?\)\s*", "", title, flags=re.I)
    title = re.sub(r"\s*\(Full\s*OST\)\s*", "", title, flags=re.I)
    title = re.sub(r"\s*\(Music\s*Video\)\s*", "", title, flags=re.I)
    title = re.sub(r"\s*\(Lyrical\s*Video\)\s*", "", title, flags=re.I)
    title = re.sub(r"\s*\[[^\]]*\]\s*", "", title)
    title = re.sub(r"\s*\|\|.*", "", title)
    title = re.sub(r"\s*\uff5c.*", "", title)
    return title.strip()


def get_meta(url: str):
    info = subprocess.run(
        ["yt-dlp", "--print", "%(title)s", "--print", "%(uploader)s", url],
        capture_output=True, text=True, check=True
    )
    lines = info.stdout.strip().splitlines()
    raw_title = lines[0] if lines else "Unknown"
    uploader = lines[1] if len(lines) > 1 else "Unknown"
    title = clean_title(raw_title)
    return title, uploader


def download_audio(url: str, outdir: str):
    subprocess.run(
        ["yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "0",
         "-o", f"{outdir}/%(title)s.%(ext)s", url],
        check=True
    )


def load_json(path: str):
    with open(path) as f:
        return json.load(f)


def save_json(path: str, data: dict):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def main():
    parser = argparse.ArgumentParser(description="Download a song and add to playlist")
    parser.add_argument("url", help="YouTube / SoundCloud URL")
    parser.add_argument("playlist", nargs="?", default="fav", help="Playlist name (default: fav)")
    args = parser.parse_args()

    playlist = args.playlist
    playlist_dir = os.path.join(MEDIA_DIR, playlist)
    os.makedirs(playlist_dir, exist_ok=True)

    title, uploader = get_meta(args.url)
    print(f"Downloading: {title} by {uploader}")

    download_audio(args.url, playlist_dir)

    found = None
    for f in os.listdir(playlist_dir):
        if f.endswith(".mp3") and not any(
            t["filename"] == f for t in load_json(SONGS_JSON).get(playlist, [])
        ):
            found = f
            break

    if not found:
        for f in os.listdir(playlist_dir):
            if f.endswith(".mp3"):
                found = f
                break

    if not found:
        print("ERROR: no new MP3 found in", playlist_dir)
        sys.exit(1)

    filename = found
    path = os.path.join(playlist_dir, filename)
    entry = {
        "filename": filename,
        "path": path,
        "artist": uploader,
        "title": title,
        "playlist": playlist,
    }

    songs = load_json(SONGS_JSON)
    if playlist not in songs:
        songs[playlist] = []
    songs[playlist].append(entry)

    if "All Songs" not in songs:
        songs["All Songs"] = []
    songs["All Songs"].append(entry)

    save_json(SONGS_JSON, songs)
    print(f"Added to songs.json: {title}")

    subprocess.run(["git", "add", "-A"], check=True)
    subprocess.run(
        ["git", "commit", "-m", f"add song: {title} [{playlist}]"],
        check=True,
    )
    subprocess.run(["git", "push"], check=True)
    print("Pushed to GitHub.")


if __name__ == "__main__":
    main()
