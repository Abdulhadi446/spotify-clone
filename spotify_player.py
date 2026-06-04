#!/usr/bin/env python3
"""Spotify Clone — Desktop music player (customtkinter + pygame)."""

import json, os, random, threading, time
from pathlib import Path
import customtkinter as ctk
import pygame

BASE_DIR = Path(__file__).parent
SONGS_JSON = BASE_DIR / "songs.json"
MEDIA_DIR = BASE_DIR / "media"

pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)


class SongLibrary:
    def __init__(self):
        self.data = {}
        self.all_songs = []
        self.playlists = []
        self._load()

    def _load(self):
        with open(SONGS_JSON) as f:
            self.data = json.load(f)
        self.playlists = [k for k in self.data if k != "All Songs"]
        self.all_songs = self.data.get("All Songs", [])

    def get_playlist(self, name):
        return self.data.get(name, [])

    def get_all(self):
        return self.all_songs


class AudioPlayer:
    def __init__(self):
        self.current_track = None
        self.playing = False
        self.shuffle = False
        self.repeat = False
        self.volume = 0.7
        self.queue = []
        self.queue_idx = -1
        pygame.mixer.music.set_volume(self.volume)

    def load(self, track):
        path = BASE_DIR / track["path"]
        if not path.exists():
            return False
        pygame.mixer.music.load(str(path))
        self.current_track = track
        return True

    def play(self, track=None):
        if track:
            if not self.load(track):
                return
        pygame.mixer.music.play()
        self.playing = True

    def pause(self):
        pygame.mixer.music.pause()
        self.playing = False

    def unpause(self):
        pygame.mixer.music.unpause()
        self.playing = True

    def stop(self):
        pygame.mixer.music.stop()
        self.playing = False

    def seek(self, pos):
        pygame.mixer.music.play(start=pos)

    def get_pos(self):
        return pygame.mixer.music.get_pos() / 1000

    def set_volume(self, v):
        self.volume = max(0, min(1, v))
        pygame.mixer.music.set_volume(self.volume)

    def next_idx(self, length):
        if self.shuffle:
            return random.randrange(length)
        return (self.queue_idx + 1) % length if length else 0

    def prev_idx(self, length):
        if self.shuffle:
            return random.randrange(length)
        return (self.queue_idx - 1 + length) % length if length else 0

    def set_queue(self, tracks, start=0):
        self.queue = tracks
        self.queue_idx = start

    def is_busy(self):
        return pygame.mixer.music.get_busy()


class SpotifyApp(ctk.CTk):
    W = 1100
    H = 700

    COLORS = {
        "bg": "#121212",
        "surface": "#181818",
        "s2": "#232323",
        "s3": "#2a2a2a",
        "green": "#1DB954",
        "text": "#ffffff",
        "muted": "#a7a7a7",
    }

    GRADS = [
        ("#1DB954", "#116930"), ("#3D4F7C", "#1f2d4e"), ("#8E44AD", "#5b2c6f"),
        ("#C0392B", "#7b241c"), ("#D35400", "#784212"), ("#1A5276", "#154360"),
        ("#117A65", "#0e6251"), ("#1F618D", "#154360"), ("#633974", "#4a235a"),
        ("#B7950B", "#7d6608"), ("#1E8449", "#145a32"), ("#922B21", "#641e16"),
    ]

    def __init__(self):
        super().__init__()
        self.lib = SongLibrary()
        self.player = AudioPlayer()
        self.liked = set()
        self._progress_active = True

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.title("My Music")
        self.geometry(f"{self.W}x{self.H}")
        self.minsize(800, 500)
        self.configure(fg_color=self.COLORS["bg"])

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self._build_sidebar()
        self._build_main()
        self._build_player()

        self.select_playlist("All Songs")
        self._start_progress_thread()

    def _grad(self, i):
        g = self.GRADS[i % len(self.GRADS)]
        return f"linear-gradient(135deg, {g[0]}, {g[1]})"

    # ── Sidebar ──

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, fg_color="#000000", corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(self.sidebar, text="My Music", font=("DM Sans", 22, "bold"),
                      text_color=self.COLORS["text"]).pack(pady=(20, 16), padx=18, anchor="w")

        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=8, pady=(0, 8))
        self.nav_btn = ctk.CTkButton(nav_frame, text="🏠  All Songs", anchor="w",
            fg_color="transparent", text_color=self.COLORS["muted"], hover_color=self.COLORS["s2"],
            font=("DM Sans", 13), command=lambda: self.select_playlist("All Songs"))
        self.nav_btn.pack(fill="x")

        lib_frame = ctk.CTkFrame(self.sidebar, fg_color=self.COLORS["surface"], corner_radius=8)
        lib_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        header = ctk.CTkFrame(lib_frame, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(header, text="📚  Playlists", font=("DM Sans", 11, "bold"),
                      text_color=self.COLORS["muted"]).pack(side="left")

        scroll = ctk.CTkScrollableFrame(lib_frame, fg_color="transparent", scrollbar_button_color=self.COLORS["s3"])
        scroll.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.pl_container = scroll

        self._render_playlists()

    def _render_playlists(self):
        for w in self.pl_container.winfo_children():
            w.destroy()
        for name in self.lib.playlists:
            count = len(self.lib.get_playlist(name))
            btn = ctk.CTkButton(self.pl_container, text=f"  📁  {name}",
                anchor="w", fg_color="transparent", text_color=self.COLORS["muted"],
                hover_color=self.COLORS["s2"], font=("DM Sans", 13),
                command=lambda n=name: self.select_playlist(n))
            btn.pack(fill="x", pady=1)
            sub = ctk.CTkLabel(btn, text=f"Playlist · {count} song{'s' if count != 1 else ''}",
                font=("DM Sans", 10), text_color=self.COLORS["muted"])
            sub.pack(anchor="w", padx=28, pady=(0, 4))

    # ── Main area ──

    def _build_main(self):
        self.main_frame = ctk.CTkFrame(self, fg_color=self.COLORS["bg"], corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # hero
        self.hero_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=200)
        self.hero_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.hero_frame.grid_propagate(False)

        hero_inner = ctk.CTkFrame(self.hero_frame, fg_color="transparent")
        hero_inner.pack(fill="both", expand=True)
        hero_inner.grid_columnconfigure(1, weight=1)

        self.hero_art = ctk.CTkLabel(hero_inner, text="🎵", font=("DM Sans", 60),
            fg_color=self.COLORS["s3"], corner_radius=8, width=180, height=180)
        self.hero_art.grid(row=0, column=0, rowspan=2, padx=(0, 20), pady=5)

        self.hero_type = ctk.CTkLabel(hero_inner, text="PLAYLIST", font=("DM Sans", 11, "bold"),
            text_color=self.COLORS["muted"])
        self.hero_type.grid(row=0, column=1, sticky="sw", pady=(30, 0))

        self.hero_title = ctk.CTkLabel(hero_inner, text="All Songs", font=("DM Sans", 36, "bold"),
            text_color=self.COLORS["text"])
        self.hero_title.grid(row=1, column=1, sticky="nw")

        # actions bar
        actions = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        actions.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        self.play_btn = ctk.CTkButton(actions, text="▶", width=50, height=50,
            fg_color=self.COLORS["green"], hover_color="#1ed760", text_color="#000",
            font=("DM Sans", 24, "bold"), corner_radius=25,
            command=self._toggle_play)
        self.play_btn.pack(side="left", padx=(0, 10))

        self.shuffle_btn = ctk.CTkButton(actions, text="🔀", width=36, height=36,
            fg_color="transparent", hover_color=self.COLORS["s2"], font=("DM Sans", 16),
            text_color=self.COLORS["muted"], command=self._toggle_shuffle)
        self.shuffle_btn.pack(side="left")

        # track list
        self.track_container = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent",
            scrollbar_button_color=self.COLORS["s3"])
        self.track_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 100))

        # header
        hdr = ctk.CTkFrame(self.track_container, fg_color="transparent", height=30)
        hdr.pack(fill="x", pady=(0, 4))
        for col, w in [("#", 40), ("Title", 1), ("Album", 1), ("⏱", 60)]:
            lbl = ctk.CTkLabel(hdr, text=col, font=("DM Sans", 11, "bold"),
                text_color=self.COLORS["muted"])
            if col == "#":
                lbl.pack(side="left", padx=(10, 0))
            elif col == "⏱":
                lbl.pack(side="right", padx=(0, 10))
            else:
                lbl.pack(side="left", fill="x", expand=True, padx=10)

        sep = ctk.CTkFrame(self.track_container, height=1, fg_color="rgba(255,255,255,0.06)")
        sep.pack(fill="x")

        self.track_list_frame = ctk.CTkFrame(self.track_container, fg_color="transparent")
        self.track_list_frame.pack(fill="both", expand=True)

    def _render_tracks(self, tracks):
        for w in self.track_list_frame.winfo_children():
            w.destroy()
        for i, t in enumerate(tracks):
            row = ctk.CTkFrame(self.track_list_frame, fg_color="transparent", height=48)
            row.pack(fill="x", pady=1)
            row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=self.COLORS["s2"]))
            row.bind("<Leave>", lambda e, r=row: r.configure(fg_color="transparent"))

            num = ctk.CTkLabel(row, text=str(i + 1), width=30, font=("DM Sans", 13),
                text_color=self.COLORS["muted"])
            num.pack(side="left", padx=(14, 0))

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=10)

            title_lbl = ctk.CTkLabel(info, text=t["title"], font=("DM Sans", 14, "bold"),
                text_color=self.COLORS["text"], anchor="w")
            title_lbl.pack(fill="x")
            artist_lbl = ctk.CTkLabel(info, text=t["artist"], font=("DM Sans", 12),
                text_color=self.COLORS["muted"], anchor="w")
            artist_lbl.pack(fill="x")

            album_lbl = ctk.CTkLabel(row, text=t.get("playlist", ""), font=("DM Sans", 12),
                text_color=self.COLORS["muted"])
            album_lbl.pack(side="left", fill="x", expand=True, padx=10)

            dur = ctk.CTkLabel(row, text="—", width=50, font=("DM Sans", 12),
                text_color=self.COLORS["muted"])
            dur.pack(side="right", padx=(0, 14))

            row.bind("<Button-1>", lambda e, idx=i, tr=tracks: self._play_at(idx, tr))

    # ── Player bar ──

    def _build_player(self):
        self.player_frame = ctk.CTkFrame(self, height=88, fg_color=self.COLORS["surface"],
            corner_radius=0)
        self.player_frame.grid(row=1, column=1, sticky="ew")
        self.player_frame.grid_propagate(False)
        self.player_frame.grid_columnconfigure(1, weight=1)

        # left: track info
        left = ctk.CTkFrame(self.player_frame, fg_color="transparent", width=220)
        left.grid(row=0, column=0, sticky="w", padx=14)
        left.grid_propagate(False)

        self.p_thumb = ctk.CTkLabel(left, text="🎵", font=("DM Sans", 24),
            fg_color=self.COLORS["s3"], corner_radius=4, width=52, height=52)
        self.p_thumb.pack(side="left", padx=(0, 10))

        info = ctk.CTkFrame(left, fg_color="transparent")
        info.pack(side="left")
        self.p_title = ctk.CTkLabel(info, text="Select a song", font=("DM Sans", 13, "bold"),
            text_color=self.COLORS["text"])
        self.p_title.pack(anchor="w")
        self.p_artist = ctk.CTkLabel(info, text="—", font=("DM Sans", 11),
            text_color=self.COLORS["muted"])
        self.p_artist.pack(anchor="w")

        # center: controls + progress
        center = ctk.CTkFrame(self.player_frame, fg_color="transparent")
        center.grid(row=0, column=1, sticky="ew")
        center.grid_columnconfigure(0, weight=1)

        ctrl_frame = ctk.CTkFrame(center, fg_color="transparent")
        ctrl_frame.pack(pady=(6, 2))

        self.shuffle_ctrl = ctk.CTkButton(ctrl_frame, text="🔀", width=30, height=30,
            fg_color="transparent", hover_color=self.COLORS["s2"], font=("DM Sans", 14),
            text_color=self.COLORS["muted"], command=self._toggle_shuffle)
        self.shuffle_ctrl.pack(side="left", padx=6)

        ctk.CTkButton(ctrl_frame, text="⏮", width=30, height=30,
            fg_color="transparent", hover_color=self.COLORS["s2"], font=("DM Sans", 16),
            text_color=self.COLORS["muted"], command=self._prev).pack(side="left", padx=6)

        self.pp_ctrl = ctk.CTkButton(ctrl_frame, text="▶", width=36, height=36,
            fg_color=self.COLORS["text"], hover_color="#e0e0e0", text_color="#000",
            font=("DM Sans", 18), corner_radius=18, command=self._toggle_play)
        self.pp_ctrl.pack(side="left", padx=6)

        ctk.CTkButton(ctrl_frame, text="⏭", width=30, height=30,
            fg_color="transparent", hover_color=self.COLORS["s2"], font=("DM Sans", 16),
            text_color=self.COLORS["muted"], command=self._next).pack(side="left", padx=6)

        self.repeat_ctrl = ctk.CTkButton(ctrl_frame, text="🔁", width=30, height=30,
            fg_color="transparent", hover_color=self.COLORS["s2"], font=("DM Sans", 14),
            text_color=self.COLORS["muted"], command=self._toggle_repeat)
        self.repeat_ctrl.pack(side="left", padx=6)

        # progress bar
        prog_frame = ctk.CTkFrame(center, fg_color="transparent")
        prog_frame.pack(fill="x", padx=20, pady=(0, 6))

        self.time_cur = ctk.CTkLabel(prog_frame, text="0:00", font=("DM Sans", 10),
            text_color=self.COLORS["muted"], width=30)
        self.time_cur.pack(side="left")

        self.progress_bar = ctk.CTkProgressBar(prog_frame, height=4,
            fg_color=self.COLORS["s3"], progress_color=self.COLORS["muted"],
            corner_radius=2)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=6)
        self.progress_bar.set(0)

        self.time_tot = ctk.CTkLabel(prog_frame, text="0:00", font=("DM Sans", 10),
            text_color=self.COLORS["muted"], width=30)
        self.time_tot.pack(side="left")

        # right: volume
        right = ctk.CTkFrame(self.player_frame, fg_color="transparent", width=160)
        right.grid(row=0, column=2, sticky="e", padx=14)
        right.grid_propagate(False)

        self.vol_slider = ctk.CTkSlider(right, from_=0, to=1, number_of_steps=100,
            width=70, fg_color=self.COLORS["s3"], button_color=self.COLORS["text"],
            button_hover_color=self.COLORS["muted"], command=self._set_vol)
        self.vol_slider.pack(side="right")
        self.vol_slider.set(self.player.volume)

    # ── Playback logic ──

    def select_playlist(self, name):
        tracks = self.lib.get_playlist(name) if name != "All Songs" else self.lib.get_all()
        if not tracks:
            return
        self.hero_title.configure(text=name)
        self._render_tracks(tracks)
        self.player.set_queue(tracks)
        self.player.queue_idx = -1

    def _play_at(self, idx, tracks):
        self.player.set_queue(tracks, start=idx)
        self.player.play(tracks[idx])
        self._update_player_ui(tracks[idx])
        self.pp_ctrl.configure(text="⏸")

    def _toggle_play(self):
        if self.player.queue_idx < 0 and self.player.queue:
            self._play_at(0, self.player.queue)
            return
        if self.player.playing:
            self.player.pause()
            self.pp_ctrl.configure(text="▶")
            self.play_btn.configure(text="▶")
        else:
            self.player.unpause()
            self.pp_ctrl.configure(text="⏸")
            self.play_btn.configure(text="⏸")

    def _next(self):
        if not self.player.queue:
            return
        idx = self.player.next_idx(len(self.player.queue))
        track = self.player.queue[idx]
        self.player.play(track)
        self._update_player_ui(track)
        self.pp_ctrl.configure(text="⏸")
        self.play_btn.configure(text="⏸")

    def _prev(self):
        if not self.player.queue:
            return
        if self.player.get_pos() > 3:
            self.player.seek(0)
            return
        idx = self.player.prev_idx(len(self.player.queue))
        track = self.player.queue[idx]
        self.player.play(track)
        self._update_player_ui(track)
        self.pp_ctrl.configure(text="⏸")
        self.play_btn.configure(text="⏸")

    def _toggle_shuffle(self):
        self.player.shuffle = not self.player.shuffle
        color = self.COLORS["green"] if self.player.shuffle else self.COLORS["muted"]
        self.shuffle_btn.configure(text_color=color)
        self.shuffle_ctrl.configure(text_color=color)

    def _toggle_repeat(self):
        self.player.repeat = not self.player.repeat
        color = self.COLORS["green"] if self.player.repeat else self.COLORS["muted"]
        self.repeat_ctrl.configure(text_color=color)

    def _set_vol(self, val):
        self.player.set_volume(val)

    def _update_player_ui(self, track):
        self.p_title.configure(text=track["title"])
        self.p_artist.configure(text=track["artist"])

    def _format_time(self, secs):
        if secs is None or secs < 0:
            return "0:00"
        m = int(secs // 60)
        s = int(secs % 60)
        return f"{m}:{s:02d}"

    def _start_progress_thread(self):
        def poll():
            while self._progress_active:
                try:
                    if self.player.playing and self.player.current_track:
                        pos = self.player.get_pos()
                        self.progress_bar.set(pos / 300 if pos > 0 else 0)
                        self.time_cur.configure(text=self._format_time(pos))
                    self.update_idletasks()
                except:
                    pass
                time.sleep(0.3)

        t = threading.Thread(target=poll, daemon=True)
        t.start()

    def run(self):
        self.mainloop()


if __name__ == "__main__":
    app = SpotifyApp()
    app.run()
