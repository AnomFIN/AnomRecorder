"""Tkinter UI for the AnomRecorder desktop client.

Why this design:
- Declarative widget factories keep layout readable despite feature density.
- Functional helpers isolate CV + IO work from Tkinter event loop.
- Playback and recording loops run on the same timer to remain responsive.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox, simpledialog, ttk

from ..core.detection import PersonDetector
from ..core.humanize import format_bytes, format_percentage, format_timestamp
from ..services.camera import list_cameras
from ..services.recording import RecorderConfig, RollingRecorder
from .theme import PALETTE, apply_dark_theme
from ..utils.resources import find_resource
from ..utils.zoom import ZoomState, crop_zoom

# Where code learns and brands scale.

LOGGER = logging.getLogger("anomrecorder.ui")

UPDATE_INTERVAL_MS = 33
PLAYBACK_BASE_INTERVAL = 1.0 / 30.0


@dataclass
class EventItem:
    id: int
    name: str
    path: str
    start: Optional[datetime]
    end: Optional[datetime]
    duration: Optional[float]
    persons_max: int = 0
    note: str = ""


class CameraApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("AnomRecorder — AnomFIN")
        apply_dark_theme(root)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.logger = LOGGER
        self.logger.info("app-init")

        self.num_cams = tk.IntVar(value=1)
        self.enable_motion = tk.BooleanVar(value=True)
        self.enable_person = tk.BooleanVar(value=True)

        self.zoom_states = [ZoomState(min_factor=0.5), ZoomState(min_factor=0.5)]
        self.zoom_labels = [tk.StringVar(value="1.0x"), tk.StringVar(value="1.0x")]
        self.pan_offsets = [[0, 0], [0, 0]]  # [x, y] offset for each camera
        self.panning_enabled = [tk.BooleanVar(value=False), tk.BooleanVar(value=False)]

        self.recording_indicators = [tk.StringVar(value="●"), tk.StringVar(value="●")]
        self.is_recording = [False, False]
        
        self.caps: List[Optional[cv2.VideoCapture]] = [None, None]
        self.indices: List[Optional[int]] = [None, None]
        self.frame_imgs: List[Optional[ImageTk.PhotoImage]] = [None, None]
        self.last_frames_bgr: List[Optional[np.ndarray]] = [None, None]
        self.camera_list: List[Any] = []

        self.record_dir = Path(os.getcwd()) / "recordings"
        self.record_dir.mkdir(parents=True, exist_ok=True)
        self.recorders = [
            RollingRecorder(RecorderConfig(out_dir=self.record_dir, cam_slot=0)),
            RollingRecorder(RecorderConfig(out_dir=self.record_dir, cam_slot=1)),
        ]

        self.events: List[EventItem] = []
        self.event_counter = 0

        self.storage_limit_gb = tk.DoubleVar(value=5.0)
        self.motion_threshold = tk.DoubleVar(value=0.05)
        self.logo_alpha = tk.DoubleVar(value=0.25)
        self.logo_path: Optional[str] = find_resource("logo.png")
        self.logo_bgra: Optional[np.ndarray] = None

        self._detector = PersonDetector()
        self._bgsubs = [cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=16, detectShadows=True) for _ in range(2)]

        self.status_var = tk.StringVar(value="Valitse kamera listasta.")
        self.usage_label_var = tk.StringVar(value="Käyttöaste: 0%, 0 MB / 5 GB")
        self.motion_thresh_label_var = tk.StringVar(value="5 %")
        
        self.hotkeys_enabled = tk.BooleanVar(value=True)
        self.autoreconnect_enabled = tk.BooleanVar(value=True)
        self.camera_refresh_in_progress = False
        self.logo_preview_img: Optional[ImageTk.PhotoImage] = None

        self.playback_vc: Optional[cv2.VideoCapture] = None
        self.playback_state = tk.StringVar(value="stopped")
        self.playback_speed = tk.DoubleVar(value=1.0)
        self.playback_path: Optional[str] = None
        self.playback_img: Optional[ImageTk.PhotoImage] = None
        self.playback_last_tick = time.time()

        self._load_settings()
        self.motion_thresh_label_var.set(f"{int(float(self.motion_threshold.get()) * 100)} %")
        self._build_layout()
        self._load_logo(self.logo_path)
        self._update_usage_label()
        self._load_recordings_on_startup()
        self._bind_hotkeys()
        self.refresh_cameras()
        self.update_layout()
        self.root.after(UPDATE_INTERVAL_MS, self.update_frames)
        self.root.after(2000, self._tick_usage)

    # ------------------------------------------------------------------
    # UI construction
    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.live_tab = ttk.Frame(self.notebook)
        self.events_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.live_tab, text="Live")
        self.notebook.add(self.events_tab, text="Tallenteet")
        self.notebook.add(self.settings_tab, text="Asetukset")

        self._build_live_tab()
        self._build_events_tab()
        self._build_settings_tab()

    def _build_live_tab(self) -> None:
        top_bar = ttk.Frame(self.live_tab)
        top_bar.pack(fill=tk.X)

        ttk.Label(top_bar, text="Kamera 1").pack(side=tk.LEFT)
        self.camera_combo1 = ttk.Combobox(top_bar, width=14, state="readonly")
        self.camera_combo1.pack(side=tk.LEFT, padx=(6, 12))
        self.camera_combo1.bind("<<ComboboxSelected>>", lambda _e: self.on_select_camera(0))

        ttk.Label(top_bar, text="Kamera 2").pack(side=tk.LEFT)
        self.camera_combo2 = ttk.Combobox(top_bar, width=14, state="readonly")
        self.camera_combo2.pack(side=tk.LEFT, padx=(6, 12))
        self.camera_combo2.bind("<<ComboboxSelected>>", lambda _e: self.on_select_camera(1))

        ttk.Label(top_bar, text="Näkymä").pack(side=tk.LEFT, padx=(12, 4))
        ttk.Radiobutton(top_bar, text="1", variable=self.num_cams, value=1, command=self.update_layout).pack(side=tk.LEFT)
        ttk.Radiobutton(top_bar, text="2", variable=self.num_cams, value=2, command=self.update_layout).pack(side=tk.LEFT)
        ttk.Radiobutton(top_bar, text="Tallenteet", variable=self.num_cams, value=3, command=self.select_recordings_view).pack(side=tk.LEFT)

        self.refresh_btn = ttk.Button(top_bar, text="🔄 Päivitä", command=self.refresh_cameras)
        self.refresh_btn.pack(side=tk.LEFT, padx=(16, 0))
        ttk.Button(top_bar, text="📷 Kuvakaappaus", command=self.save_snapshot).pack(side=tk.LEFT, padx=(8, 0))
        
        # Recording indicators
        indicator_frame = ttk.Frame(top_bar)
        indicator_frame.pack(side=tk.LEFT, padx=(16, 0))
        ttk.Label(indicator_frame, text="Tallentaa:").pack(side=tk.LEFT)
        self.rec_indicator1 = ttk.Label(indicator_frame, textvariable=self.recording_indicators[0], foreground="green")
        self.rec_indicator1.pack(side=tk.LEFT, padx=2)
        self.rec_indicator2 = ttk.Label(indicator_frame, textvariable=self.recording_indicators[1], foreground="green")
        self.rec_indicator2.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(top_bar, text="Sulje", command=self.on_close, style="Accent.TButton").pack(side=tk.RIGHT)

        options = ttk.Frame(self.live_tab)
        options.pack(fill=tk.X, pady=(12, 0))
        ttk.Checkbutton(options, text="Liikkeentunnistus", variable=self.enable_motion).pack(side=tk.LEFT)
        ttk.Checkbutton(options, text="Henkilötunnistus", variable=self.enable_person).pack(side=tk.LEFT, padx=(12, 0))

        zoom_frame = ttk.Frame(self.live_tab)
        zoom_frame.pack(fill=tk.X, pady=(12, 0))
        self._build_zoom_controls(zoom_frame, 0)
        self._build_zoom_controls(zoom_frame, 1)

        self.video_area = ttk.Frame(self.live_tab)
        self.video_area.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.video_area.columnconfigure(0, weight=1)
        self.video_area.columnconfigure(1, weight=1)

        self.frame_label1 = ttk.Label(self.video_area)
        self.frame_label1.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.frame_label1.bind("<Button-1>", lambda e: self._on_video_click(0, e))
        self.frame_label1.bind("<B1-Motion>", lambda e: self._on_video_drag(0, e))
        
        self.frame_label2 = ttk.Label(self.video_area)
        self.frame_label2.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        self.frame_label2.bind("<Button-1>", lambda e: self._on_video_click(1, e))
        self.frame_label2.bind("<B1-Motion>", lambda e: self._on_video_drag(1, e))

        ttk.Label(self.live_tab, textvariable=self.status_var, foreground=PALETTE["muted"]).pack(anchor=tk.W, pady=(12, 0))

    def _build_zoom_controls(self, parent: ttk.Frame, slot: int) -> None:
        block = ttk.Frame(parent)
        block.pack(side=tk.LEFT, padx=(0 if slot == 0 else 24, 0))
        ttk.Label(block, text=f"Zoom {slot + 1}").pack(side=tk.LEFT)
        ttk.Button(block, text="🔍−", width=4, command=lambda s=slot: self._update_zoom(s, "out")).pack(side=tk.LEFT, padx=2)
        ttk.Button(block, text="🔍+", width=4, command=lambda s=slot: self._update_zoom(s, "in")).pack(side=tk.LEFT, padx=2)
        ttk.Button(block, text="Reset", width=6, command=lambda s=slot: self._update_zoom(s, "reset")).pack(side=tk.LEFT, padx=2)
        ttk.Label(block, textvariable=self.zoom_labels[slot]).pack(side=tk.LEFT, padx=(6, 0))
        
        # Pan controls
        pan_frame = ttk.Frame(block)
        pan_frame.pack(side=tk.LEFT, padx=(12, 0))
        ttk.Label(pan_frame, text="Pan:").pack(side=tk.LEFT)
        ttk.Checkbutton(pan_frame, text="🖱️", variable=self.panning_enabled[slot], 
                       command=lambda s=slot: self._toggle_panning(s)).pack(side=tk.LEFT)
        ttk.Button(pan_frame, text="↑", width=2, command=lambda s=slot: self._pan(s, 0, -20)).pack(side=tk.LEFT, padx=1)
        ttk.Button(pan_frame, text="↓", width=2, command=lambda s=slot: self._pan(s, 0, 20)).pack(side=tk.LEFT, padx=1)
        ttk.Button(pan_frame, text="←", width=2, command=lambda s=slot: self._pan(s, -20, 0)).pack(side=tk.LEFT, padx=1)
        ttk.Button(pan_frame, text="→", width=2, command=lambda s=slot: self._pan(s, 20, 0)).pack(side=tk.LEFT, padx=1)

    def _build_events_tab(self) -> None:
        top = ttk.Frame(self.events_tab)
        top.pack(fill=tk.X)
        ttk.Label(top, text="Tallenteet").pack(side=tk.LEFT)
        ttk.Button(top, text="Avaa kansio", command=self._open_recordings_folder).pack(side=tk.LEFT, padx=8)
        ttk.Button(top, text="Lisää merkintä", command=self.add_event_note).pack(side=tk.LEFT, padx=8)

        body = ttk.Frame(self.events_tab)
        body.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        columns = ("nimi", "alku", "kesto", "henkilot", "merkinta")
        self.events_view = ttk.Treeview(body, columns=columns, show="headings", height=14)
        self.events_view.heading("nimi", text="Nimi")
        self.events_view.heading("alku", text="Alkuaika")
        self.events_view.heading("kesto", text="Kesto (s)")
        self.events_view.heading("henkilot", text="Henkilöt")
        self.events_view.heading("merkinta", text="Merkinnät")
        self.events_view.column("nimi", width=200)
        self.events_view.column("alku", width=160)
        self.events_view.column("kesto", width=80, anchor="center")
        self.events_view.column("henkilot", width=80, anchor="center")
        self.events_view.column("merkinta", width=260)
        self.events_view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(body, orient=tk.VERTICAL, command=self.events_view.yview)
        self.events_view.configure(yscroll=scroll.set)
        scroll.pack(side=tk.LEFT, fill=tk.Y)
        self.events_view.bind("<<TreeviewSelect>>", self.on_select_event)

        playback_panel = ttk.Frame(self.events_tab)
        playback_panel.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        controls = ttk.Frame(playback_panel)
        controls.pack(fill=tk.X, pady=(0, 12))
        ttk.Button(controls, text="Play", command=self.playback_play, style="Accent.TButton").pack(side=tk.LEFT, padx=4)
        ttk.Button(controls, text="Pause", command=self.playback_pause).pack(side=tk.LEFT, padx=4)
        ttk.Button(controls, text="Stop", command=self.playback_stop).pack(side=tk.LEFT, padx=4)
        ttk.Button(controls, text="0.5x", command=lambda: self._set_playback_speed(0.5)).pack(side=tk.LEFT, padx=4)
        ttk.Button(controls, text="1x", command=lambda: self._set_playback_speed(1.0)).pack(side=tk.LEFT, padx=4)
        ttk.Button(controls, text="2x", command=lambda: self._set_playback_speed(2.0)).pack(side=tk.LEFT, padx=4)
        ttk.Label(controls, textvariable=self.playback_state, foreground=PALETTE["muted"]).pack(side=tk.RIGHT)

        self.playback_label = ttk.Label(playback_panel)
        self.playback_label.pack()

    def _build_settings_tab(self) -> None:
        outer = ttk.Frame(self.settings_tab)
        outer.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        storage = ttk.Labelframe(outer, text="Tallennustila")
        storage.pack(fill=tk.X, padx=8, pady=8)
        ttk.Label(storage, text="Raja (GB)").pack(side=tk.LEFT)
        entry = ttk.Entry(storage, textvariable=self.storage_limit_gb, width=8)
        entry.pack(side=tk.LEFT, padx=8)
        ttk.Button(storage, text="Tyhjennä", command=self._clear_recordings).pack(side=tk.LEFT, padx=6)
        ttk.Label(storage, textvariable=self.usage_label_var).pack(side=tk.RIGHT)

        branding = ttk.Labelframe(outer, text="Brändäys")
        branding.pack(fill=tk.X, padx=8, pady=8)
        
        logo_row = ttk.Frame(branding)
        logo_row.pack(fill=tk.X, pady=4)
        self.logo_path_var = tk.StringVar(value=self.logo_path or "")
        ttk.Label(logo_row, text="Logo").pack(side=tk.LEFT)
        ttk.Entry(logo_row, textvariable=self.logo_path_var, width=35).pack(side=tk.LEFT, padx=8)
        ttk.Button(logo_row, text="📁 Valitse", command=self._choose_logo).pack(side=tk.LEFT)
        
        # Logo preview
        preview_row = ttk.Frame(branding)
        preview_row.pack(fill=tk.X, pady=4)
        ttk.Label(preview_row, text="Esikatselu:").pack(side=tk.LEFT)
        self.logo_preview_label = ttk.Label(preview_row, text="Ei logoa valittu")
        self.logo_preview_label.pack(side=tk.LEFT, padx=8)
        
        alpha_row = ttk.Frame(branding)
        alpha_row.pack(fill=tk.X, pady=4)
        ttk.Label(alpha_row, text="Läpinäkyvyys").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Scale(alpha_row, from_=0.0, to=1.0, orient=tk.HORIZONTAL, variable=self.logo_alpha).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        motion = ttk.Labelframe(outer, text="Liikekynnys")
        motion.pack(fill=tk.X, padx=8, pady=8)
        ttk.Label(motion, text="Kynnys").pack(side=tk.LEFT)
        ttk.Scale(motion, from_=0.0, to=0.3, orient=tk.HORIZONTAL, variable=self.motion_threshold, command=lambda _v: self._on_motion_change()).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        ttk.Label(motion, textvariable=self.motion_thresh_label_var).pack(side=tk.LEFT, padx=(8, 0))
        
        # Hotkeys and autoreconnect settings
        advanced = ttk.Labelframe(outer, text="Lisäasetukset")
        advanced.pack(fill=tk.X, padx=8, pady=8)
        ttk.Checkbutton(advanced, text="Näppäinoikotiet käytössä", variable=self.hotkeys_enabled).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(advanced, text="Automaattinen yhdistäminen uudelleen", variable=self.autoreconnect_enabled).pack(anchor=tk.W, pady=2)
        
        # Save button
        save_frame = ttk.Frame(outer)
        save_frame.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(save_frame, text="💾 Tallenna asetukset", command=self._save_settings_safe, style="Accent.TButton").pack(side=tk.LEFT)

        ttk.Label(outer, text="Kamerajärjestelmä by AnomFIN", foreground=PALETTE["muted"]).pack(anchor=tk.E, pady=(12, 0))

    # ------------------------------------------------------------------
    # Camera management
    def refresh_cameras(self) -> None:
        """Non-blocking camera refresh that doesn't stop recording or freeze UI."""
        if self.camera_refresh_in_progress:
            self.status_var.set("Kameran päivitys jo käynnissä...")
            return
        
        self.camera_refresh_in_progress = True
        self.refresh_btn.configure(state="disabled", text="⏳ Päivitetään...")
        
        def _refresh_worker():
            try:
                cams = list_cameras()
                # Schedule UI update on main thread
                self.root.after(0, lambda: self._apply_camera_list(cams))
            except Exception as exc:
                self.logger.exception("camera-refresh-failed", exc_info=exc)
                self.root.after(0, lambda: self._show_error("Kameran päivitys epäonnistui", str(exc)))
            finally:
                self.root.after(0, lambda: self._finish_camera_refresh())
        
        thread = threading.Thread(target=_refresh_worker, daemon=True, name="CameraRefresh")
        thread.start()
    
    def _apply_camera_list(self, cams: List[Any]) -> None:
        """Apply camera list to UI (called on main thread)."""
        self.camera_list = cams
        labels = [name for name, _ in cams]
        self.camera_combo1["values"] = labels
        self.camera_combo2["values"] = labels
        if labels:
            if self.camera_combo1.current() == -1:
                self.camera_combo1.current(0)
                self.on_select_camera(0)
            if self.num_cams.get() >= 2 and self.camera_combo2.current() == -1 and len(labels) > 1:
                self.camera_combo2.current(1)
                self.on_select_camera(1)
            self.status_var.set("Kamerat: " + ", ".join(labels))
        else:
            self.status_var.set("Kameraa ei löydy. Kytke USB-kamera ja päivitä.")
    
    def _finish_camera_refresh(self) -> None:
        """Cleanup after camera refresh."""
        self.camera_refresh_in_progress = False
        self.refresh_btn.configure(state="normal", text="🔄 Päivitä")

    def update_layout(self) -> None:
        if self.num_cams.get() == 1:
            self.frame_label2.grid_remove()
            self.stop_camera(1)
        elif self.num_cams.get() == 2:
            self.frame_label2.grid()
            if self.camera_combo2.current() == -1 and self.camera_combo2["values"] and len(self.camera_combo2["values"]) > 1:
                self.camera_combo2.current(1)
                self.on_select_camera(1)
        elif self.num_cams.get() == 3:
            self.notebook.select(self.events_tab)

    def on_select_camera(self, slot: int) -> None:
        combo = self.camera_combo1 if slot == 0 else self.camera_combo2
        selection = combo.current()
        if selection == -1 or selection >= len(self.camera_list):
            self.stop_camera(slot)
            return
        _, index = self.camera_list[selection]
        self.start_camera(slot, index)

    def start_camera(self, slot: int, index: int) -> None:
        if self.indices[slot] == index and self.caps[slot] is not None:
            return
        self.stop_camera(slot)
        
        try:
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            if not cap.isOpened():
                self.status_var.set(f"Kamera {slot + 1}: avaaminen epäonnistui")
                cap.release()
                if self.autoreconnect_enabled.get():
                    self._schedule_reconnect(slot, index, attempt=1)
                return
            self.caps[slot] = cap
            self.indices[slot] = index
            self.status_var.set("Live-katselu käynnissä")
        except Exception as exc:
            self.logger.exception(f"camera-start-failed-slot{slot}", exc_info=exc)
            self._show_error("Kameran avaaminen epäonnistui", str(exc))
            if self.autoreconnect_enabled.get():
                self._schedule_reconnect(slot, index, attempt=1)
    
    def _schedule_reconnect(self, slot: int, index: int, attempt: int, max_attempts: int = 5) -> None:
        """Schedule camera reconnection with exponential backoff."""
        if attempt > max_attempts:
            self.status_var.set(f"Kamera {slot + 1}: yhdistäminen epäonnistui {max_attempts} yrityksen jälkeen")
            return
        
        delay_ms = min(1000 * (2 ** (attempt - 1)), 30000)  # Max 30 seconds
        self.status_var.set(f"Kamera {slot + 1}: yritetään yhdistää uudelleen {attempt}/{max_attempts}...")
        self.root.after(delay_ms, lambda: self._attempt_reconnect(slot, index, attempt, max_attempts))
    
    def _attempt_reconnect(self, slot: int, index: int, attempt: int, max_attempts: int) -> None:
        """Attempt to reconnect to camera."""
        if self.caps[slot] is not None:
            return  # Already connected
        
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        if cap.isOpened():
            self.caps[slot] = cap
            self.indices[slot] = index
            self.status_var.set(f"Kamera {slot + 1}: yhdistetty uudelleen!")
            self.logger.info(f"camera-reconnect-success-slot{slot}", extra={"attempt": attempt})
        else:
            cap.release()
            self._schedule_reconnect(slot, index, attempt + 1, max_attempts)

    def stop_camera(self, slot: int) -> None:
        if self.caps[slot] is not None:
            try:
                self.caps[slot].release()
            except Exception:
                self.logger.warning("cap-release-failed", exc_info=True)
        self.caps[slot] = None
        self.indices[slot] = None

    # ------------------------------------------------------------------
    # Frame pipeline
    def update_frames(self) -> None:
        if not self.root.winfo_exists():
            return
        self._update_playback_if_needed()
        labels = [self.frame_label1, self.frame_label2]
        for slot in range(2):
            label = labels[slot]
            if slot == 1 and self.num_cams.get() == 1:
                label.configure(image="")
                self.frame_imgs[slot] = None
                continue
            cap = self.caps[slot]
            if cap is None:
                continue
            
            try:
                ok, frame = cap.read()
                if not ok:
                    # Camera disconnected - attempt reconnect if enabled
                    if self.autoreconnect_enabled.get() and self.indices[slot] is not None:
                        self.logger.warning(f"camera-read-failed-slot{slot}")
                        self.stop_camera(slot)
                        self._schedule_reconnect(slot, self.indices[slot], attempt=1)
                    continue
                
                self.last_frames_bgr[slot] = frame.copy()
                detections = self._detector.detect(frame) if self.enable_person.get() else []
                annotated = self._annotate(slot, frame, detections)
                zoomed = crop_zoom(annotated, self.zoom_states[slot].factor, tuple(self.pan_offsets[slot]))
                display = cv2.resize(zoomed, (960, 540)) if zoomed.shape[1] > 960 else zoomed
                frame_rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.frame_imgs[slot] = imgtk
                label.configure(image=imgtk)

                motion_trigger = False
                if self.enable_motion.get():
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    fg = self._bgsubs[slot].apply(gray)
                    lvl = float((fg > 0).sum()) / float(fg.size)
                    motion_trigger = lvl > float(self.motion_threshold.get())
                person_count = len(detections)

                new_event, finished_event = self.recorders[slot].update(annotated, motion_trigger, person_count)
                
                # Update recording indicator
                was_recording = self.is_recording[slot]
                self.is_recording[slot] = self.recorders[slot]._recording
                if self.is_recording[slot] != was_recording:
                    self._update_recording_indicator(slot)
                
                if new_event:
                    self._handle_new_event(new_event)
                if finished_event:
                    self._handle_finished_event(finished_event)
            
            except Exception as exc:
                self.logger.exception(f"frame-update-error-slot{slot}", exc_info=exc)

        self.root.after(UPDATE_INTERVAL_MS, self.update_frames)

    def _annotate(self, slot: int, frame_bgr: np.ndarray, detections: List[Any]) -> np.ndarray:
        annotated = frame_bgr.copy()
        for (x, y, w, h), conf in detections:
            color = (0, 255, 0) if conf >= 0.6 else (0, 180, 255)
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
            cv2.putText(annotated, f"Henkilö {int(conf * 100)}%", (x, max(0, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(annotated, ts, (12, annotated.shape[0] - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230, 230, 230), 2, cv2.LINE_AA)
        return self._overlay_logo(annotated)

    def _handle_new_event(self, data: Dict[str, Any]) -> None:
        self.event_counter += 1
        event = EventItem(
            id=self.event_counter,
            name=f"Tallenne {self.event_counter}",
            path=data.get("path", ""),
            start=data.get("start"),
            end=None,
            duration=None,
            persons_max=0,
        )
        self.events.append(event)
        self.refresh_events_view()
        self._enforce_storage_limit()
        self.logger.info("event-start", extra={"path": event.path})

    def _handle_finished_event(self, data: Dict[str, Any]) -> None:
        for event in reversed(self.events):
            if event.path == data.get("path"):
                event.end = data.get("end")
                event.duration = data.get("duration")
                event.persons_max = data.get("persons_max", 0)
                break
        self.refresh_events_view()
        self._update_usage_label()
        self.logger.info("event-end", extra={"path": data.get("path"), "duration": data.get("duration")})

    # ------------------------------------------------------------------
    # Playback
    def _update_playback_if_needed(self) -> None:
        state = self.playback_state.get()
        if not state.startswith("playing") or self.playback_vc is None:
            return
        now = time.time()
        interval = PLAYBACK_BASE_INTERVAL / max(0.1, float(self.playback_speed.get()))
        if now - self.playback_last_tick < interval:
            return
        self.playback_last_tick = now
        ok, frame = self.playback_vc.read()
        if not ok:
            try:
                self.playback_vc.release()
            except Exception:
                self.logger.warning("playback-release-failed", exc_info=True)
            self.playback_vc = None
            self.playback_state.set("stopped")
            self.playback_label.configure(image="")
            self.playback_img = None
            return
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame_rgb.shape
        scale = min(960 / w, 540 / h, 1.0)
        if scale < 1.0:
            frame_rgb = cv2.resize(frame_rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        img = Image.fromarray(frame_rgb)
        self.playback_img = ImageTk.PhotoImage(image=img)
        self.playback_label.configure(image=self.playback_img)

    def _set_playback_speed(self, speed: float) -> None:
        self.playback_speed.set(max(0.1, min(4.0, speed)))
        self.playback_state.set(f"playing @{self.playback_speed.get():.1f}x" if self.playback_state.get().startswith("playing") else self.playback_state.get())

    def playback_play(self) -> None:
        if self.playback_path and (self.playback_vc is None or not self.playback_vc.isOpened()):
            self.playback_vc = cv2.VideoCapture(self.playback_path)
        if self.playback_vc is None:
            return
        self.playback_state.set(f"playing @{self.playback_speed.get():.1f}x")
        self.playback_last_tick = 0.0

    def playback_pause(self) -> None:
        if self.playback_state.get().startswith("playing"):
            self.playback_state.set("paused")

    def playback_stop(self) -> None:
        if self.playback_vc is not None:
            try:
                self.playback_vc.release()
            except Exception:
                self.logger.warning("playback-release-failed", exc_info=True)
        self.playback_vc = None
        self.playback_state.set("stopped")
        self.playback_label.configure(image="")
        self.playback_img = None

    def on_select_event(self, _event=None) -> None:
        selection = self.events_view.selection()
        if not selection:
            return
        path = selection[0]
        self.playback_stop()
        self.playback_path = path
        self.playback_vc = cv2.VideoCapture(path)
        if not self.playback_vc.isOpened():
            messagebox.showerror("Virhe", "Tallenteen avaaminen epäonnistui")
            self.playback_vc = None
            return
        self.playback_state.set("paused")
        self.notebook.select(self.events_tab)

    # ------------------------------------------------------------------
    # Recording list
    def refresh_events_view(self) -> None:
        for item in self.events_view.get_children():
            self.events_view.delete(item)
        for event in self.events:
            start_str = format_timestamp(event.start) if event.start else ""
            dur = f"{event.duration:.1f}" if event.duration else ""
            persons = str(event.persons_max or 0)
            self.events_view.insert("", tk.END, iid=event.path, values=(event.name, start_str, dur, persons, event.note))

    def add_event_note(self) -> None:
        selection = self.events_view.selection()
        if not selection:
            messagebox.showinfo("Huom", "Valitse ensin tallenne.")
            return
        note = simpledialog.askstring("Lisää merkintä", "Kirjoita merkintä")
        if note is None:
            return
        for event in self.events:
            if event.path == selection[0]:
                event.note = note.strip()
                break
        self.refresh_events_view()

    # ------------------------------------------------------------------
    # Settings & persistence
    def _settings_path(self) -> Path:
        return Path(os.getcwd()) / "settings.json"

    def _load_settings(self) -> None:
        try:
            data = json.loads(Path(self._settings_path()).read_text(encoding="utf-8"))
        except Exception:
            return
        self.storage_limit_gb.set(float(data.get("storage_limit_gb", self.storage_limit_gb.get())))
        self.logo_path = data.get("logo_path") or self.logo_path
        self.logo_alpha.set(float(data.get("logo_alpha", self.logo_alpha.get())))
        self.motion_threshold.set(float(data.get("motion_threshold", self.motion_threshold.get())))
        self.hotkeys_enabled.set(bool(data.get("hotkeys_enabled", True)))
        self.autoreconnect_enabled.set(bool(data.get("autoreconnect_enabled", True)))

    def _save_settings(self) -> None:
        """Internal save settings (used by sliders, etc)."""
        payload = {
            "storage_limit_gb": float(self.storage_limit_gb.get()),
            "logo_path": self.logo_path or "",
            "logo_alpha": float(self.logo_alpha.get()),
            "motion_threshold": float(self.motion_threshold.get()),
            "hotkeys_enabled": bool(self.hotkeys_enabled.get()),
            "autoreconnect_enabled": bool(self.autoreconnect_enabled.get()),
        }
        try:
            Path(self._settings_path()).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            self.logger.warning("settings-save-failed", exc_info=True)
    
    def _save_settings_safe(self) -> None:
        """Safe settings save from UI button - doesn't interrupt recording."""
        try:
            # Validate storage limit
            value = float(self.storage_limit_gb.get())
            if value <= 0:
                raise ValueError("Storage limit must be > 0")
            
            # Save all settings atomically
            self._save_settings()
            self._enforce_storage_limit()
            self._update_usage_label()
            
            # Show success message
            messagebox.showinfo("Tallennettu", "Asetukset tallennettu onnistuneesti!")
            self.logger.info("settings-saved-by-user")
        except ValueError as exc:
            messagebox.showerror("Virhe", f"Virheellinen arvo: {exc}")
        except Exception as exc:
            self.logger.exception("settings-save-error", exc_info=exc)
            self._show_error("Asetusten tallennus epäonnistui", str(exc))

    def _save_limit(self) -> None:
        try:
            value = float(self.storage_limit_gb.get())
            if value <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Virhe", "Anna kelvollinen raja (GB > 0)")
            return
        self._enforce_storage_limit()
        self._update_usage_label()
        self._save_settings()

    def _clear_recordings(self) -> None:
        if not messagebox.askyesno("Vahvista", "Poistetaanko kaikki tallenteet?"):
            return
        for file in self.record_dir.glob("*"):
            if file.is_file():
                try:
                    file.unlink()
                except Exception:
                    self.logger.warning("delete-failed", extra={"path": str(file)}, exc_info=True)
        self.events.clear()
        self.refresh_events_view()
        self._update_usage_label()

    def _choose_logo(self) -> None:
        path = filedialog.askopenfilename(title="Valitse logo", filetypes=[("Kuvat", "*.png;*.jpg;*.jpeg;*.bmp"), ("Kaikki", "*.*")])
        if not path:
            return
        self.logo_path = path
        self.logo_path_var.set(path)
        self._load_logo(path)
        self._update_logo_preview()

    def _update_logo_preview(self) -> None:
        """Update logo preview in settings tab."""
        if self.logo_bgra is None:
            self.logo_preview_label.configure(image="", text="Ei logoa valittu")
            self.logo_preview_img = None
            return
        
        try:
            # Create preview image (max 100x100)
            h, w = self.logo_bgra.shape[:2]
            scale = min(100 / w, 100 / h, 1.0)
            new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
            preview_bgra = cv2.resize(self.logo_bgra, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            # Convert BGRA to RGB
            b, g, r, a = cv2.split(preview_bgra)
            preview_rgb = cv2.merge((r, g, b))
            
            img = Image.fromarray(preview_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.logo_preview_img = imgtk
            self.logo_preview_label.configure(image=imgtk, text="")
        except Exception as exc:
            self.logger.warning("logo-preview-failed", exc_info=exc)
            self.logo_preview_label.configure(image="", text="Esikatseluvirhe")

    def _load_logo(self, path: Optional[str]) -> None:
        self.logo_bgra = None
        if not path:
            return
        try:
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img is None:
                return
            if img.shape[2] == 3:
                b, g, r = cv2.split(img)
                a = np.full_like(b, 255)
                img = cv2.merge((b, g, r, a))
            self.logo_bgra = img
        except Exception as exc:
            self.logger.warning("logo-load-failed", exc_info=exc)

    def _overlay_logo(self, frame_bgr: np.ndarray) -> np.ndarray:
        if self.logo_bgra is None:
            return frame_bgr
        overlay = self.logo_bgra
        h, w = frame_bgr.shape[:2]
        target_w = max(1, int(w * 0.18))
        scale = target_w / overlay.shape[1]
        new_size = (target_w, max(1, int(overlay.shape[0] * scale)))
        resized = cv2.resize(overlay, new_size, interpolation=cv2.INTER_AREA)
        oh, ow = resized.shape[:2]
        x = w - ow - 20
        y = 20
        if x < 0 or y < 0 or x + ow > w or y + oh > h:
            return frame_bgr
        roi = frame_bgr[y:y + oh, x:x + ow]
        alpha = (resized[..., 3].astype("float32") / 255.0) * float(self.logo_alpha.get())
        alpha_bg = 1.0 - alpha
        for c in range(3):
            roi[..., c] = (alpha * resized[..., c] + alpha_bg * roi[..., c]).astype("uint8")
        frame_bgr[y:y + oh, x:x + ow] = roi
        return frame_bgr

    def _on_motion_change(self) -> None:
        self.motion_thresh_label_var.set(f"{int(float(self.motion_threshold.get()) * 100)} %")
        self._save_settings()

    def _dir_size_bytes(self, path: Path) -> int:
        total = 0
        for file in path.glob("*"):
            if file.is_file():
                try:
                    total += file.stat().st_size
                except Exception:
                    self.logger.warning("stat-failed", extra={"path": str(file)}, exc_info=True)
        return total

    def _update_usage_label(self) -> None:
        used = self._dir_size_bytes(self.record_dir)
        limit_b = int(max(0.0001, float(self.storage_limit_gb.get())) * (1024 ** 3))
        pct = format_percentage(used, limit_b)
        self.usage_label_var.set(f"Käyttöaste: {pct}, {format_bytes(used)} / {format_bytes(limit_b)}")

    def _tick_usage(self) -> None:
        self._update_usage_label()
        if self.root.winfo_exists():
            self.root.after(2000, self._tick_usage)

    def _enforce_storage_limit(self) -> None:
        limit_b = int(max(0.0001, float(self.storage_limit_gb.get())) * (1024 ** 3))
        files = []
        for file in self.record_dir.glob("*.avi"):
            try:
                files.append((file.stat().st_mtime, file, file.stat().st_size))
            except Exception:
                self.logger.warning("stat-failed", extra={"path": str(file)}, exc_info=True)
        files.sort()
        total = sum(size for _, _, size in files)
        idx = 0
        while total > limit_b and idx < len(files):
            _, file, size = files[idx]
            try:
                file.unlink()
                total -= size
            except Exception:
                self.logger.warning("unlink-failed", extra={"path": str(file)}, exc_info=True)
            idx += 1

    # ------------------------------------------------------------------
    # Misc actions
    def _update_zoom(self, slot: int, direction: str) -> None:
        state = self.zoom_states[slot]
        if direction == "in":
            state.zoom_in()
        elif direction == "out":
            state.zoom_out()
        else:
            state.reset()
            self.pan_offsets[slot] = [0, 0]  # Reset pan on zoom reset
        self.zoom_labels[slot].set(f"{state.factor:.1f}x")
    
    def _pan(self, slot: int, dx: int, dy: int) -> None:
        """Pan the zoomed area by dx, dy pixels."""
        self.pan_offsets[slot][0] += dx
        self.pan_offsets[slot][1] += dy
        # Clamp pan offsets (rough bounds)
        max_offset = 500
        self.pan_offsets[slot][0] = max(-max_offset, min(max_offset, self.pan_offsets[slot][0]))
        self.pan_offsets[slot][1] = max(-max_offset, min(max_offset, self.pan_offsets[slot][1]))
    
    def _toggle_panning(self, slot: int) -> None:
        """Toggle panning mode for video area."""
        enabled = self.panning_enabled[slot].get()
        cursor = "fleur" if enabled else ""
        label = self.frame_label1 if slot == 0 else self.frame_label2
        label.configure(cursor=cursor)
    
    def _on_video_click(self, slot: int, event) -> None:
        """Handle click on video area for panning start."""
        if self.panning_enabled[slot].get():
            self._drag_start = (event.x, event.y)
    
    def _on_video_drag(self, slot: int, event) -> None:
        """Handle drag on video area for panning."""
        if self.panning_enabled[slot].get() and hasattr(self, '_drag_start'):
            dx = event.x - self._drag_start[0]
            dy = event.y - self._drag_start[1]
            self._pan(slot, -dx, -dy)
            self._drag_start = (event.x, event.y)
    
    def _update_recording_indicator(self, slot: int) -> None:
        """Update recording indicator color."""
        is_rec = self.is_recording[slot]
        indicator = self.rec_indicator1 if slot == 0 else self.rec_indicator2
        color = "red" if is_rec else "green"
        text = "●"
        indicator.configure(foreground=color)
        self.recording_indicators[slot].set(text)
    
    def _show_error(self, title: str, message: str) -> None:
        """Show error dialog."""
        try:
            messagebox.showerror(title, message)
        except Exception:
            self.logger.warning("error-dialog-failed")
    
    def _bind_hotkeys(self) -> None:
        """Bind keyboard shortcuts."""
        if not self.hotkeys_enabled.get():
            return
        
        # Space: toggle recording (not implemented as recording is automatic)
        # R: refresh cameras
        self.root.bind("<r>", lambda e: self.refresh_cameras() if not self._is_typing() else None)
        self.root.bind("<R>", lambda e: self.refresh_cameras() if not self._is_typing() else None)
        
        # +/- for zoom
        self.root.bind("<plus>", lambda e: self._update_zoom(0, "in") if not self._is_typing() else None)
        self.root.bind("<minus>", lambda e: self._update_zoom(0, "out") if not self._is_typing() else None)
        self.root.bind("<equal>", lambda e: self._update_zoom(0, "in") if not self._is_typing() else None)  # + without shift
        
        # Arrow keys for panning
        self.root.bind("<Up>", lambda e: self._pan(0, 0, -20) if not self._is_typing() else None)
        self.root.bind("<Down>", lambda e: self._pan(0, 0, 20) if not self._is_typing() else None)
        self.root.bind("<Left>", lambda e: self._pan(0, -20, 0) if not self._is_typing() else None)
        self.root.bind("<Right>", lambda e: self._pan(0, 20, 0) if not self._is_typing() else None)
        
        # Escape: reset zoom/pan or stop actions
        self.root.bind("<Escape>", lambda e: self._handle_escape())
    
    def _is_typing(self) -> bool:
        """Check if user is typing in an entry widget."""
        try:
            focused = self.root.focus_get()
            return isinstance(focused, (tk.Entry, tk.Text, ttk.Entry))
        except Exception:
            return False
    
    def _handle_escape(self) -> None:
        """Handle escape key - reset zoom/pan."""
        for slot in range(2):
            self._update_zoom(slot, "reset")
            self.panning_enabled[slot].set(False)
            self._toggle_panning(slot)
    
    def _load_recordings_on_startup(self) -> None:
        """Load existing recordings from disk on app startup."""
        try:
            files = sorted(self.record_dir.glob("recording_*.avi"), key=lambda f: f.stat().st_mtime, reverse=True)
            for file in files:
                try:
                    # Parse timestamp from filename
                    name = file.stem
                    parts = name.split("_")
                    if len(parts) >= 3:
                        date_str = parts[-2]
                        time_str = parts[-1]
                        dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                        
                        # Get file size for duration estimation
                        stat = file.stat()
                        duration = stat.st_size / (1024 * 1024 * 5)  # Rough estimate: ~5MB/sec
                        
                        self.event_counter += 1
                        event = EventItem(
                            id=self.event_counter,
                            name=file.name,
                            path=str(file),
                            start=dt,
                            end=None,
                            duration=duration if duration > 0 else None,
                            persons_max=0,
                        )
                        self.events.append(event)
                except Exception as exc:
                    self.logger.warning(f"failed-to-load-recording: {file}", exc_info=exc)
            
            if self.events:
                self.refresh_events_view()
                self.logger.info(f"loaded-{len(self.events)}-recordings-on-startup")
        except Exception as exc:
            self.logger.exception("recordings-load-failed", exc_info=exc)

    def save_snapshot(self) -> None:
        slot = 0 if self.indices[0] is not None else (1 if self.indices[1] is not None else None)
        if slot is None or self.last_frames_bgr[slot] is None:
            messagebox.showinfo("Huom", "Ei kuvaa tallennettavana.")
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.record_dir / f"snapshot_cam{slot}_{ts}.png"
        cv2.imwrite(str(path), self.last_frames_bgr[slot])
        messagebox.showinfo("Tallennettu", f"Kuvakaappaus tallennettu:\n{path}")

    def _open_recordings_folder(self) -> None:
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(self.record_dir))
            elif sys.platform == "darwin":
                os.system(f"open '{self.record_dir}'")
            else:
                os.system(f"xdg-open '{self.record_dir}' >/dev/null 2>&1 &")
        except Exception as exc:
            messagebox.showerror("Virhe", f"Kansion avaaminen epäonnistui: {exc}")

    def select_recordings_view(self) -> None:
        self.notebook.select(self.events_tab)

    def on_close(self) -> None:
        self.logger.info("shutdown")
        for cap in self.caps:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass
        if self.playback_vc is not None:
            try:
                self.playback_vc.release()
            except Exception:
                pass
        self.root.destroy()


__all__ = ["CameraApp"]
