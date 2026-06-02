#!/usr/bin/env python3
"""
Local helper server for the Spotify clone.
Handles:
  POST /download  – downloads a YouTube URL via yt-dlp into media/<playlist>
  GET  /playlists – returns folder list + file list as JSON
  GET  /          – serves index.html (and static files)

Run with:  python3 server.py
Then open: http://localhost:8765
"""

import os, json, subprocess, threading, time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

BASE   = os.path.dirname(os.path.abspath(__file__))
MEDIA  = os.path.join(BASE, "media")

# ── Same SONGS mapping as your tagger script ──────────────────────────────────
SONGS = {
    "Aap Ka Aana":             ("Dj Saurabh",                    "Aap Ka Aana Dil Dhadkana"),
    "Nadaaniyan":              ("Akshath",                        "Nadaaniyan"),
    "AFSOS":                   ("Anuv Jain ft. AP Dhillon",       "Afsos"),
    "ALAG AASMAAN":            ("Anuv Jain",                      "Alag Aasmaan"),
    "HUSN":                    ("Anuv Jain",                      "Husn"),
    "JO TUM MERE HO":          ("Anuv Jain",                      "Jo Tum Mere Ho"),
    "Meem Se Mohabbat":        ("Asim Azhar & Qirat Haider",      "Baat"),
    "BYE":                     ("Aditya Bhardwaj",                "Bye"),
    "CHAL DIYE TUM KAHAN":     ("AUR",                            "Chal Diye Tum Kahan"),
    "Ishq Di Chashni":         ("Qirat Haider",                   "Ho Gya Hai Ishq"),
    "I'm Done":                ("Maan Panu",                      "I'm Done"),
    "Ishq Official":           ("Amir Ameer",                     "Ishq"),
    "Ishq Wala Love":          ("Neeti Mohan",                    "Ishq Wala Love"),
    "Jeena Jeena":             ("Sachin-Jigar ft. Atif Aslam",    "Jeena Jeena"),
    "Boyfriend":               ("Karan Aujla ft. Ikky",           "Boyfriend"),
    "For A Reason":            ("Karan Aujla ft. Ikky",           "For A Reason"),
    "Khwab":                   ("Iqlipse Nova ft. Aditya A",      "Khwab"),
    "Mere Liye Tum Kaafi Ho":  ("Tanishk-Vayu",                   "Mere Liye Tum Kaafi Ho"),
    "Paro x Maand":            ("Aditya Rikhari",                  "Paro x Maand"),
    "Qurbaniyan":              ("Asim Azhar",                     "Qurbaniyan"),
    "Raastah":                 ("AUR ft. Taimour Baig",           "Raastah"),
    "Ranjheya Ve":             ("Zain Zohaib",                    "Ranjheya Ve"),
    "Sahiba (Full Audio)":     ("Aditya Rikhari",                  "Sahiba"),
    "Sahiba (Music Video)":    ("Jasleen Royal ft. Stebin Ben",   "Sahiba"),
    "Shikayat":                ("AUR",                            "Shikayat"),
    "One Love":                ("Shubh",                          "One Love"),
    "Sometimes":               ("AUR",                            "Sometimes"),
    "Ishq Murshid":            ("Ahmed Jahanzeb",                 "Tera Mera Hai Pyar"),
    "Tu Hai Kahan":            ("AUR",                            "Tu Hai Kahan"),
    "Tu Hain Toh":             ("Hunny, Bunny, Sagar",            "Tu Hain Toh"),
    "Tum Hi Ho":               ("Arijit Singh",                   "Tum Hi Ho"),
    "WAVY":                    ("Karan Aujla",                    "Wavy"),
    "Ye Tune Kya Kiya":        ("Pritam",                         "Ye Tune Kya Kiya"),
    "MERI ZINDAGI":            ("Anuv Jain",                      "Meri Zindagi Hai Tu"),
}

def resolve_meta(filename):
    """Return (artist, title) from SONGS map or fall back to filename parse."""
    name = filename.replace(".mp3", "")
    for keyword, (artist, title) in SONGS.items():
        if keyword.lower() in name.lower():
            return artist, title
    # fallback: simple parse
    import re
    m = re.match(r'^(.+?)\s*[-–]\s*(.+)', name)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "Unknown Artist", name

def scan_library():
    """Return playlists dict: { 'All Songs': [...], 'Chill': [...], ... }"""
    result = {}
    all_tracks = []

    # root-level mp3s → All Songs
    root_files = []
    for f in sorted(os.listdir(MEDIA)):
        fp = os.path.join(MEDIA, f)
        if os.path.isfile(fp) and f.lower().endswith(".mp3"):
            artist, title = resolve_meta(f)
            root_files.append({"filename": f, "path": f"media/{f}",
                                "artist": artist, "title": title, "playlist": "All Songs"})
    all_tracks.extend(root_files)
    result["All Songs"] = root_files

    # subfolders → named playlists
    for entry in sorted(os.listdir(MEDIA)):
        ep = os.path.join(MEDIA, entry)
        if os.path.isdir(ep):
            pl_tracks = []
            for f in sorted(os.listdir(ep)):
                if f.lower().endswith(".mp3"):
                    artist, title = resolve_meta(f)
                    track = {"filename": f, "path": f"media/{entry}/{f}",
                             "artist": artist, "title": title, "playlist": entry}
                    pl_tracks.append(track)
                    all_tracks.append(track)
            result[entry] = pl_tracks  # show even if empty

    # inject all_tracks as first key
    final = {"All Songs": all_tracks}
    for k, v in result.items():
        if k != "All Songs":
            final[k] = v
    return final


# active download jobs: id -> {status, progress, error}
jobs = {}
job_lock = threading.Lock()

def run_download(job_id, url, dest_dir):
    def worker():
        with job_lock:
            jobs[job_id] = {"status": "running", "progress": "Starting…", "error": None}
        try:
            cmd = [
                "yt-dlp",
                "-x", "--audio-format", "mp3",
                "--audio-quality", "0",
                "-o", os.path.join(dest_dir, "%(title)s.%(ext)s"),
                "--no-playlist",
                url
            ]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True)
            last = "Downloading…"
            for line in proc.stdout:
                line = line.strip()
                if line:
                    last = line[-120:]   # keep last 120 chars for display
                with job_lock:
                    jobs[job_id]["progress"] = last
            proc.wait()
            if proc.returncode == 0:
                with job_lock:
                    jobs[job_id]["status"] = "done"
                    jobs[job_id]["progress"] = "Done!"
            else:
                with job_lock:
                    jobs[job_id]["status"] = "error"
                    jobs[job_id]["error"] = f"yt-dlp exited with code {proc.returncode}"
        except FileNotFoundError:
            with job_lock:
                jobs[job_id]["status"] = "error"
                jobs[job_id]["error"] = "yt-dlp not found. Install it: pip install yt-dlp"
        except Exception as e:
            with job_lock:
                jobs[job_id]["status"] = "error"
                jobs[job_id]["error"] = str(e)
    threading.Thread(target=worker, daemon=True).start()


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args): pass   # silence request logs

    def send_json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path

        if path == "/playlists":
            self.send_json(scan_library())
        elif path == "/job":
            qs = parse_qs(parsed.query)
            jid = qs.get("id", [None])[0]
            with job_lock:
                info = jobs.get(jid, {"status": "unknown"})
            self.send_json(info)
        elif path == "/folders":
            folders = ["All Songs"] + [
                d for d in sorted(os.listdir(MEDIA))
                if os.path.isdir(os.path.join(MEDIA, d))
            ]
            self.send_json(folders)
        else:
            # serve static files
            super().do_GET()

    def do_POST(self):
        if self.path == "/download":
            length = int(self.headers.get("Content-Length", 0))
            body   = json.loads(self.rfile.read(length))
            url    = body.get("url", "").strip()
            folder = body.get("folder", "All Songs").strip()

            if not url:
                self.send_json({"error": "No URL provided"}, 400); return

            if folder == "All Songs":
                dest = MEDIA
            else:
                dest = os.path.join(MEDIA, folder)
                os.makedirs(dest, exist_ok=True)

            job_id = str(int(time.time() * 1000))
            run_download(job_id, url, dest)
            self.send_json({"job_id": job_id})

        elif self.path == "/create-playlist":
            length = int(self.headers.get("Content-Length", 0))
            body   = json.loads(self.rfile.read(length))
            name   = body.get("name", "").strip()
            if not name or "/" in name or ".." in name:
                self.send_json({"error": "Invalid name"}, 400); return
            dest = os.path.join(MEDIA, name)
            os.makedirs(dest, exist_ok=True)
            self.send_json({"ok": True, "folder": name})

        else:
            self.send_json({"error": "Not found"}, 404)


if __name__ == "__main__":
    os.chdir(BASE)
    port = 8765
    print(f"🎵  Spotify Clone running at  http://localhost:{port}")
    print(f"    Serving files from: {BASE}")
    print(f"    Press Ctrl+C to stop.\n")
    HTTPServer(("localhost", port), Handler).serve_forever()
