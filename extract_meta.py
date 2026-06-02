#!/usr/bin/env python3
import os
import re
import json
import sys
from mutagen.id3 import ID3, TIT2, TPE1, TALB, ID3NoHeaderError
from mutagen.mp3 import MP3

def clean_name(name):
    name = re.sub(r'\s*\(Official[^)]*\)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\(Lyrics?\)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\(Full Audio\)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\[Full OST\]', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\(Official Music Video\)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\|[^|]*$', '', name)
    name = name.strip()
    return name

def extract_metadata(filepath):
    filename = os.path.basename(filepath)
    name = os.path.splitext(filename)[0]
    title, artist, album = '', '', ''

    try:
        tags = ID3(filepath)
        if tags.get('TIT2'):
            title = str(tags['TIT2'])
        if tags.get('TPE1'):
            artist = str(tags['TPE1'])
        if tags.get('TALB'):
            album = str(tags['TALB'])
    except ID3NoHeaderError:
        pass
    except Exception:
        pass

    if not title:
        title = name
    if not artist:
        dash_match = re.split(r'\s*[-–]\s*', title, maxsplit=1)
        if len(dash_match) == 2:
            artist = clean_name(dash_match[0])
            title = clean_name(dash_match[1])
        else:
            pipe_match = re.split(r'\s*[|｜]\s*', title, maxsplit=1)
            if len(pipe_match) == 2:
                artist = clean_name(pipe_match[0])
                title = clean_name(pipe_match[1])
            else:
                artist = 'Unknown Artist'
                title = clean_name(title)
    else:
        title = clean_name(title)

    duration = 0
    try:
        audio = MP3(filepath)
        duration = int(audio.info.length)
    except Exception:
        pass

    return {
        'filename': filename,
        'title': title,
        'artist': artist,
        'album': album,
        'duration': duration
    }

def scan_directory(media_dir):
    tracks = []
    for f in sorted(os.listdir(media_dir)):
        if f.lower().endswith('.mp3'):
            filepath = os.path.join(media_dir, f)
            meta = extract_metadata(filepath)
            tracks.append(meta)
    return tracks

if __name__ == '__main__':
    media_dir = sys.argv[1] if len(sys.argv) > 1 else 'media'
    if not os.path.isdir(media_dir):
        print(f"Error: '{media_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    tracks = scan_directory(media_dir)
    print(json.dumps(tracks, indent=2, ensure_ascii=False))
    print(f"\n// Found {len(tracks)} tracks", file=sys.stderr)
