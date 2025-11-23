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
from typing import Any, Dict, List, Optional, Union

import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox, simpledialog, ttk

from ..core.detection import PersonDetector
from ..core.humanize import format_bytes, format_percentage, format_timestamp
from ..services.camera import list_cameras
from ..services.ip_camera import IPCamera
from ..services.recording import RecorderConfig, RollingRecorder
from .theme import PALETTE, apply_dark_theme
from .ip_camera_dialog import show_ip_camera_dialog
from ..utils.resources import find_resource
from ..utils.zoom import ZoomState, crop_zoom
from ..utils.hotkeys import HotkeyConfig
from ..utils.reconnect import ReconnectState

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
        
        # Make window resizable with constraints
        self.root.minsize(1024, 600)
        self.root.maxsize(2560, 1440)
        self.root.geometry("1280x800")
        
        apply_dark_theme(root)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Bind keyboard shortcuts
        self.root.bind("<plus>", lambda e: self._hotkey_zoom_in())
        self.root.bind("<minus>", lambda e: self._hotkey_zoom_out())
        self.root.bind("<Left>", lambda e: self._hotkey_pan_left())
        self.root.bind("<Right>", lambda e: self._hotkey_pan_right())
        self.root.bind("<Up>", lambda e: self._hotkey_pan_up())
        self.root.bind("<Down>", lambda e: self._hotkey_pan_down())
        self.root.bind("r", lambda e: self.refresh_cameras())
        self.root.bind("R", lambda e: self.refresh_cameras())
        self.root.bind("<space>", lambda e: self._hotkey_toggle_recording())
        self.root.bind("<Escape>", lambda e: self._hotkey_reset_zoom())

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
        self.camera_sources: List[Optional[Union[str, int]]] = [None, None]  # Store either USB index or IP camera URL
        self.ip_cameras: List[IPCamera] = []  # Store configured IP cameras
        self.frame_imgs: List[Optional[ImageTk.PhotoImage]] = [None, None]
        self.last_frames_bgr: List[Optional[np.ndarray]] = [None, None]
        self.camera_list: List[Any] = []  # List of (name, source) tuples where source is USB index or IPCamera object
        
        # Reconnect states for each camera
        self.reconnect_states = [ReconnectState(), ReconnectState()]

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
        self.logo_preview_img: Optional[ImageTk.PhotoImage] = None
        
        # Hotkeys
        self.hotkeys = HotkeyConfig()

        self._detector = PersonDetector()
        self._bgsubs = [cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=16, detectShadows=True) for _ in range(2)]

        self.status_var = tk.StringVar(value="Valitse kamera listasta.")
        self.usage_label_var = tk.StringVar(value="Käyttöaste: 0%, 0 MB / 5 GB")
        self.motion_thresh_label_var = tk.StringVar(value="5 %")
        self.recording_indicator_var = tk.StringVar(value="● Ei tallenna")

        self.playback_vc: Optional[cv2.VideoCapture] = None
        self.playback_state = tk.StringVar(value="stopped")
        self.playback_speed = tk.DoubleVar(value=1.0)
        self.playback_path: Optional[str] = None
        self.playback_img: Optional[ImageTk.PhotoImage] = None
        self.playback_last_tick = time.time()
        
        # Refresh lock to prevent concurrent refreshes
        self._refresh_lock = threading.Lock()

        self._refreshing_cameras = False
        self._toast_window: Optional[tk.Toplevel] = None

        self._load_settings()
        self.motion_thresh_label_var.set(f"{int(float(self.motion_threshold.get()) * 100)} %")
        self._build_layout()
        self._load_logo(self.logo_path)
        self._update_logo_preview()
        self._update_usage_label()
        self._load_existing_recordings()  # Load recordings from disk
        self.refresh_cameras()
        self.update_layout()
        self._bind_hotkeys()  # Bind hotkeys
        self.root.after(UPDATE_INTERVAL_MS, self.update_frames)
        self.root.after(2000, self._tick_usage)
        self.root.after(5000, self._tick_reconnect)  # Periodic reconnect check

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

        # Recording indicator on the left
        self.recording_indicator_label = ttk.Label(
            top_bar, 
            textvariable=self.recording_indicator_var, 
            foreground="#00ff00"  # Green by default
        )
        self.recording_indicator_label.pack(side=tk.LEFT, padx=(0, 12))

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

        ttk.Button(top_bar, text="Päivitä", command=self.refresh_cameras_async).pack(side=tk.LEFT, padx=(16, 0))
        ttk.Button(top_bar, text="+ IP-kamera", command=self.add_ip_camera).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(top_bar, text="Kuvakaappaus", command=self.save_snapshot).pack(side=tk.LEFT, padx=(8, 0))
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

        # Bind arrow keys for panning
        self.root.bind("<Left>", lambda e: self._pan_active_camera(-0.05, 0))
        self.root.bind("<Right>", lambda e: self._pan_active_camera(0.05, 0))
        self.root.bind("<Up>", lambda e: self._pan_active_camera(0, -0.05))
        self.root.bind("<Down>", lambda e: self._pan_active_camera(0, 0.05))

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
        ttk.Label(block, text="Pan:").pack(side=tk.LEFT, padx=(12, 4))
        ttk.Button(block, text="←", width=3, command=lambda s=slot: self._pan_camera(s, -0.1, 0)).pack(side=tk.LEFT, padx=2)
        ttk.Button(block, text="↑", width=3, command=lambda s=slot: self._pan_camera(s, 0, -0.1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(block, text="↓", width=3, command=lambda s=slot: self._pan_camera(s, 0, 0.1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(block, text="→", width=3, command=lambda s=slot: self._pan_camera(s, 0.1, 0)).pack(side=tk.LEFT, padx=2)

    def _build_events_tab(self) -> None:
        top = ttk.Frame(self.events_tab)
        top.pack(fill=tk.X)
        ttk.Label(top, text="Tallenteet").pack(side=tk.LEFT)
        ttk.Button(top, text="Avaa kansio", command=self._open_recordings_folder).pack(side=tk.LEFT, padx=8)
        ttk.Button(top, text="Lisää merkintä", command=self.add_event_note).pack(side=tk.LEFT, padx=8)
        ttk.Button(top, text="Poista valittu", command=self._delete_selected_recording).pack(side=tk.LEFT, padx=8)
        ttk.Button(top, text="Poista kaikki", command=self._clear_recordings).pack(side=tk.LEFT, padx=8)

        body = ttk.Frame(self.events_tab)
        body.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        columns = ("nimi", "alku", "kesto", "henkilot", "merkinta")
        self.events_view = ttk.Treeview(body, columns=columns, show="headings", height=14, selectmode="extended")
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
        ttk.Label(storage, textvariable=self.usage_label_var).pack(side=tk.RIGHT)

        branding = ttk.Labelframe(outer, text="Brändäys")
        branding.pack(fill=tk.X, padx=8, pady=8)
        
        # Logo selection row
        logo_row = ttk.Frame(branding)
        logo_row.pack(fill=tk.X, padx=8, pady=8)
        self.logo_path_var = tk.StringVar(value=self.logo_path or "")
        ttk.Label(logo_row, text="Logo").pack(side=tk.LEFT)
        ttk.Entry(logo_row, textvariable=self.logo_path_var, width=40).pack(side=tk.LEFT, padx=8)
        ttk.Button(logo_row, text="Valitse", command=self._choose_logo).pack(side=tk.LEFT)
        
        # Logo preview
        preview_frame = ttk.Frame(branding)
        preview_frame.pack(fill=tk.X, padx=8, pady=8)
        ttk.Label(preview_frame, text="Esikatselu:").pack(side=tk.LEFT)
        self.logo_preview_label = ttk.Label(preview_frame, text="Ei logoa valittu")
        self.logo_preview_label.pack(side=tk.LEFT, padx=8)
        
        # Transparency slider
        alpha_row = ttk.Frame(branding)
        alpha_row.pack(fill=tk.X, padx=8, pady=8)
        ttk.Label(alpha_row, text="Läpinäkyvyys").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Scale(alpha_row, from_=0.0, to=1.0, orient=tk.HORIZONTAL, variable=self.logo_alpha, command=lambda _v: self._on_logo_alpha_change()).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        motion = ttk.Labelframe(outer, text="Liikekynnys")
        motion.pack(fill=tk.X, padx=8, pady=8)
        ttk.Label(motion, text="Kynnys").pack(side=tk.LEFT)
        ttk.Scale(motion, from_=0.0, to=0.3, orient=tk.HORIZONTAL, variable=self.motion_threshold, 
                  command=lambda _v: self._on_motion_change()).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        ttk.Label(motion, textvariable=self.motion_thresh_label_var).pack(side=tk.LEFT, padx=(8, 0))
        
        # Camera reconnect settings
        reconnect_frame = ttk.Labelframe(outer, text="Kamera-asetukset")
        reconnect_frame.pack(fill=tk.X, padx=8, pady=8)
        self.autoreconnect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(reconnect_frame, text="Automaattinen uudelleenyhdistäminen", 
                        variable=self.autoreconnect_var, 
                        command=self._on_autoreconnect_change).pack(side=tk.LEFT, padx=8, pady=8)
        
        # Hotkeys display
        hotkeys_frame = ttk.Labelframe(outer, text="Pikanäppäimet")
        hotkeys_frame.pack(fill=tk.X, padx=8, pady=8)
        self.hotkeys_text = tk.Text(hotkeys_frame, height=7, width=50, wrap=tk.WORD, 
                                     background=PALETTE["bg"], foreground=PALETTE["text"])
        self.hotkeys_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.hotkeys_text.insert("1.0", self.hotkeys.get_display_text())
        self.hotkeys_text.config(state=tk.DISABLED)
        
        # Save settings button
        save_frame = ttk.Frame(outer)
        save_frame.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(save_frame, text="Tallenna asetukset", command=self._save_settings_safely, 
                   style="Accent.TButton").pack(side=tk.LEFT)
        self.settings_status_var = tk.StringVar(value="")
        ttk.Label(save_frame, textvariable=self.settings_status_var, foreground=PALETTE["success"]).pack(side=tk.LEFT, padx=(12, 0))

        ttk.Label(outer, text="Kamerajärjestelmä by AnomFIN", foreground=PALETTE["muted"]).pack(anchor=tk.E, pady=(12, 0))

    # ------------------------------------------------------------------
    # Camera management
    def refresh_cameras_async(self) -> None:
        """Non-blocking camera refresh that doesn't stop recording."""
        if not self._refresh_lock.acquire(blocking=False):
            self.status_var.set("Päivitys jo käynnissä...")
            return
        
        def _refresh_in_thread():
            try:
                cams = list_cameras()
                # Schedule UI update in main thread
                self.root.after(0, lambda: self._update_camera_list(cams))
            except Exception as exc:
                self.logger.warning("camera-refresh-failed", exc_info=exc)
                self.root.after(0, lambda: self.status_var.set("Kameran päivitys epäonnistui"))
            finally:
                self._refresh_lock.release()
        
        thread = threading.Thread(target=_refresh_in_thread, daemon=True)
        thread.start()
        self.status_var.set("Päivitetään kameralistaa...")
    
    def _update_camera_list(self, cams: List[Any]) -> None:
        """Update camera list in UI thread, including IP cameras."""
        # Combine USB cameras and IP cameras
        combined_list = []
        
        # Add USB cameras
        for name, idx in cams:
            combined_list.append((name, idx))
        
        # Add IP cameras
        for ip_cam in self.ip_cameras:
            combined_list.append((ip_cam.name, ip_cam))
        
        self.camera_list = combined_list
        labels = [name for name, _ in combined_list]
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
            self._show_toast(f"Kamerat päivitetty: {len(labels)} löydetty", error=False)
        else:
            self.status_var.set("Kameraa ei löydy. Kytke USB-kamera tai lisää IP-kamera.")

    def refresh_cameras(self) -> None:
        """Refresh camera list without stopping active cameras."""
        try:
            cams = list_cameras()
            # Use _update_camera_list to properly merge USB and IP cameras
            self._update_camera_list(cams)
        except Exception as e:
            self.logger.error("refresh-cameras-failed", exc_info=True)
            messagebox.showerror("Virhe", f"Kameroiden päivitys epäonnistui: {str(e)}")
    
    def add_ip_camera(self) -> None:
        """Open dialog to add an IP/WiFi camera."""
        try:
            camera = show_ip_camera_dialog(self.root)
            if camera:
                # Add to IP cameras list
                self.ip_cameras.append(camera)
                self.logger.info(f"Added IP camera: {camera.name} at {camera.ip}")
                
                # Refresh camera list to include new IP camera
                cams = list_cameras()
                self._update_camera_list(cams)
                
                # Save IP cameras to config
                self._save_ip_cameras()
                
                self._show_toast(f"IP-kamera lisätty: {camera.name}", error=False)
        except Exception as e:
            self.logger.error("add-ip-camera-failed", exc_info=True)
            messagebox.showerror("Virhe", f"IP-kameran lisäys epäonnistui: {str(e)}")

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
        _, source = self.camera_list[selection]
        self.start_camera(slot, source)

    def start_camera(self, slot: int, source: Union[int, IPCamera]) -> None:
        """Start a camera from either USB index or IP camera object."""
        # Check if already started with same source
        if self.camera_sources[slot] == source and self.caps[slot] is not None:
            return
        self.stop_camera(slot)
        try:
            # Determine if source is USB index or IP camera
            if isinstance(source, IPCamera):
                # IP camera
                url = source.get_opencv_url()
                self.logger.info(f"Opening IP camera: {url}")
                cap = cv2.VideoCapture(url)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce latency for IP cameras
                self.camera_sources[slot] = source
                self.indices[slot] = None
            else:
                # USB camera
                cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.camera_sources[slot] = source
                self.indices[slot] = source
                
            if not cap.isOpened():
                self.status_var.set(f"Kamera {slot + 1}: avaaminen epäonnistui")
                cap.release()
                if isinstance(source, IPCamera):
                    messagebox.showwarning("Kamera", f"IP-kamera {slot + 1} ei vastaa. Tarkista verkkoasetukset.")
                else:
                    messagebox.showwarning("Kamera", f"Kamera {slot + 1} ei vastaa. Tarkista USB-liitäntä.")
                return
                
            self.caps[slot] = cap
            self.status_var.set("Live-katselu käynnissä")
        except Exception as e:
            self.logger.error("start-camera-failed", exc_info=True)
            messagebox.showerror("Virhe", f"Kameran {slot + 1} käynnistys epäonnistui: {str(e)}")

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
        
        # Check if any recorder is recording and update indicator
        is_any_recording = any(rec._recording for rec in self.recorders)
        if is_any_recording:
            self.recording_indicator_var.set("● Tallentaa")
            self.recording_indicator_label.configure(foreground=PALETTE["error"])
        else:
            self.recording_indicator_var.set("● Ei tallenna")
            self.recording_indicator_label.configure(foreground=PALETTE["success"])
        
        # Update individual camera recording states
        for slot in range(2):
            self.is_recording[slot] = self.recorders[slot]._recording
        
        labels = [self.frame_label1, self.frame_label2]
        for slot in range(2):
            try:
                label = labels[slot]
                if slot == 1 and self.num_cams.get() == 1:
                    label.configure(image="")
                    self.frame_imgs[slot] = None
                    continue
                cap = self.caps[slot]
                if cap is None:
                    continue
                ok, frame = cap.read()
                if not ok:
                    continue
                self.last_frames_bgr[slot] = frame.copy()
                detections = self._detector.detect(frame) if self.enable_person.get() else []
                annotated = self._annotate(slot, frame, detections)
                zoomed = crop_zoom(annotated, self.zoom_states[slot].factor, 
                                  self.zoom_states[slot].pan_x, self.zoom_states[slot].pan_y)
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
                if new_event:
                    self._handle_new_event(new_event)
                if finished_event:
                    self._handle_finished_event(finished_event)
            except Exception:
                self.logger.error("frame-update-failed", extra={"slot": slot}, exc_info=True)
                # Don't show error dialog in update loop to avoid freezing UI or spamming user with multiple dialogs.
                # Instead, just log the error and update status text for user visibility.
                if slot == 0 or (slot == 1 and self.num_cams.get() == 2):
                    self.status_var.set(f"Kamera {slot + 1}: virhe kuvan käsittelyssä")
        
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
        try:
            if self.playback_path and (self.playback_vc is None or not self.playback_vc.isOpened()):
                self.playback_vc = cv2.VideoCapture(self.playback_path)
            if self.playback_vc is None or not self.playback_vc.isOpened():
                messagebox.showwarning("Toisto", "Tallennetta ei voitu avata. Valitse tallenne listasta.")
                return
            self.playback_state.set(f"playing @{self.playback_speed.get():.1f}x")
            self.playback_last_tick = 0.0
        except Exception as e:
            self.logger.error("playback-play-failed", exc_info=True)
            messagebox.showerror("Virhe", f"Toiston käynnistys epäonnistui: {str(e)}")

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
    def _load_existing_recordings(self) -> None:
        """Load existing recordings from disk on startup."""
        try:
            existing_files = sorted(self.record_dir.glob("*.avi"), key=lambda p: p.stat().st_mtime, reverse=True)
            for file_path in existing_files:
                # Skip if already loaded
                if any(e.path == str(file_path) for e in self.events):
                    continue
                
                try:
                    stat = file_path.stat()
                    self.event_counter += 1
                    
                    # Try to parse timestamp from filename
                    start_time = None
                    try:
                        parts = file_path.stem.split("_")
                        if len(parts) >= 3:
                            date_str = parts[-2]
                            time_str = parts[-1]
                            start_time = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                    except Exception:
                        start_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    # Get video duration
                    duration = None
                    try:
                        cap = cv2.VideoCapture(str(file_path))
                        if cap.isOpened():
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                            if fps > 0:
                                duration = frame_count / fps
                            cap.release()
                    except Exception:
                        pass
                    
                    event = EventItem(
                        id=self.event_counter,
                        name=file_path.name,
                        path=str(file_path),
                        start=start_time,
                        end=None,
                        duration=duration,
                        persons_max=0,
                    )
                    self.events.append(event)
                except Exception:
                    self.logger.warning("load-recording-failed", extra={"path": str(file_path)}, exc_info=True)
            
            if self.events:
                self.refresh_events_view()
                self.logger.info("loaded-recordings", extra={"count": len(self.events)})
        except Exception as exc:
            self.logger.exception("load-recordings-failed", exc_info=exc)
    
    def _watch_recordings_folder(self) -> None:
        """Periodically check for new recordings in the folder."""
        try:
            existing_paths = {e.path for e in self.events}
            new_files = []
            
            for file_path in self.record_dir.glob("*.avi"):
                if str(file_path) not in existing_paths:
                    new_files.append(file_path)
            
            if new_files:
                for file_path in new_files:
                    try:
                        stat = file_path.stat()
                        self.event_counter += 1
                        
                        start_time = None
                        try:
                            parts = file_path.stem.split("_")
                            if len(parts) >= 3:
                                date_str = parts[-2]
                                time_str = parts[-1]
                                start_time = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                        except Exception:
                            start_time = datetime.fromtimestamp(stat.st_mtime)
                        
                        event = EventItem(
                            id=self.event_counter,
                            name=file_path.name,
                            path=str(file_path),
                            start=start_time,
                            end=None,
                            duration=None,
                            persons_max=0,
                        )
                        self.events.append(event)
                    except Exception:
                        self.logger.warning("watch-add-failed", extra={"path": str(file_path)}, exc_info=True)
                
                self.refresh_events_view()
                self._update_usage_label()
        except Exception:
            pass
        
        if self.root.winfo_exists():
            self.root.after(5000, self._watch_recordings_folder)
    
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

    def _delete_selected_recordings(self) -> None:
        """Delete selected recording(s) with confirmation."""
        selection = self.events_view.selection()
        if not selection:
            messagebox.showinfo("Huom", "Valitse vähintään yksi tallenne poistettavaksi.")
            return
        
        count = len(selection)
        msg = f"Poistetaanko {count} tallenne{'tta' if count > 1 else ''}?"
        if not messagebox.askyesno("Vahvista poisto", msg):
            return
        
        deleted_count = 0
        for path in selection:
            try:
                # Try to move to trash/recycle bin (platform-specific)
                file_path = Path(path)
                if file_path.exists():
                    if sys.platform.startswith("win"):
                        # Windows: use send2trash if available, else delete
                        try:
                            import send2trash
                            send2trash.send2trash(str(file_path))
                        except ImportError:
                            file_path.unlink()
                    else:
                        # Unix/Mac: use trash-cli or just delete
                        file_path.unlink()
                    
                    # Remove from events list
                    self.events = [e for e in self.events if e.path != path]
                    deleted_count += 1
            except Exception as exc:
                self.logger.warning("delete-recording-failed", extra={"path": path}, exc_info=True)
                messagebox.showerror("Virhe", f"Tallenteen poisto epäonnistui:\n{Path(path).name}\n{str(exc)}")
        
        if deleted_count > 0:
            self.refresh_events_view()
            self._update_usage_label()
            self._show_toast(f"{deleted_count} tallenne{'tta' if deleted_count > 1 else ''} poistettu", error=False)

    def _delete_all_recordings(self) -> None:
        """Delete all recordings with confirmation."""
        if not self.events:
            messagebox.showinfo("Huom", "Ei tallenteita poistettavaksi.")
            return
        
        if not messagebox.askyesno("Vahvista poisto", f"Poistetaanko KAIKKI {len(self.events)} tallennetta?\n\nTätä toimintoa ei voi kumota!"):
            return
        
        deleted_count = 0
        for event in list(self.events):
            try:
                file_path = Path(event.path)
                if file_path.exists():
                    file_path.unlink()
                deleted_count += 1
            except Exception:
                self.logger.warning("delete-recording-failed", extra={"path": event.path}, exc_info=True)
        
        self.events.clear()
        self.refresh_events_view()
        self._update_usage_label()
        self._show_toast(f"{deleted_count} tallennetta poistettu", error=False)

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
        if "hotkeys" in data:
            self.hotkeys = HotkeyConfig.from_dict(data["hotkeys"])
        if "autoreconnect" in data:
            reconnect_enabled = data["autoreconnect"]
            for state in self.reconnect_states:
                state.enabled = reconnect_enabled
        # Load IP cameras
        if "ip_cameras" in data:
            for cam_data in data["ip_cameras"]:
                try:
                    camera = IPCamera(
                        name=cam_data.get("name", ""),
                        url=cam_data.get("url", ""),
                        protocol=cam_data.get("protocol", "rtsp"),
                        ip=cam_data.get("ip", ""),
                        port=cam_data.get("port", 554),
                        username=cam_data.get("username"),
                        password=cam_data.get("password")
                    )
                    self.ip_cameras.append(camera)
                except Exception as e:
                    self.logger.warning(f"Failed to load IP camera: {e}")

    def _save_settings(self) -> None:
        """Internal save without user feedback."""
        payload = {
            "storage_limit_gb": float(self.storage_limit_gb.get()),
            "logo_path": self.logo_path or "",
            "logo_alpha": float(self.logo_alpha.get()),
            "motion_threshold": float(self.motion_threshold.get()),
            "hotkeys": self.hotkeys.to_dict(),
            "autoreconnect": self.reconnect_states[0].enabled,
            "ip_cameras": self._serialize_ip_cameras(),
        }
        try:
            # Atomic write: write to temp file then rename
            temp_path = Path(self._settings_path()).with_suffix('.tmp')
            temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            temp_path.replace(self._settings_path())
        except Exception:
            self.logger.warning("settings-save-failed", exc_info=True)
    
    def _serialize_ip_cameras(self) -> List[Dict[str, Any]]:
        """Serialize IP cameras for JSON storage.
        
        Security note: Passwords are stored in plain text in the local config file.
        This is acceptable for a local desktop application where:
        - Config files are stored locally per user
        - The alternative would require complex key management
        - Users should use application-specific camera passwords, not reuse important passwords
        """
        result = []
        for cam in self.ip_cameras:
            result.append({
                "name": cam.name,
                "url": cam.url,
                "protocol": cam.protocol,
                "ip": cam.ip,
                "port": cam.port,
                "username": cam.username,
                "password": cam.password  # Stored in plain text for local config
            })
        return result
    
    def _save_ip_cameras(self) -> None:
        """Save IP cameras configuration."""
        self._save_settings()
    
    def _save_settings_safely(self) -> None:
        """Save settings with user feedback, doesn't stop recording."""
        try:
            self._save_settings()
            self.settings_status_var.set("✓ Asetukset tallennettu")
            self.root.after(3000, lambda: self.settings_status_var.set(""))
            self.logger.info("settings-saved-by-user")
        except Exception as exc:
            self.logger.exception("settings-save-failed", exc_info=exc)
            messagebox.showerror("Virhe", f"Asetusten tallennus epäonnistui: {exc}")

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

    def _save_all_settings(self) -> None:
        """Save all settings atomically without disrupting recording."""
        try:
            self._save_settings()
            self._show_toast("Asetukset tallennettu onnistuneesti", error=False)
        except Exception as exc:
            self.logger.exception("settings-save-failed", exc_info=exc)
            self._show_toast(f"Asetusten tallennus epäonnistui: {str(exc)}", error=True)

    def _choose_logo(self) -> None:
        path = filedialog.askopenfilename(title="Valitse logo", filetypes=[("Kuvat", "*.png;*.jpg;*.jpeg;*.bmp"), ("Kaikki", "*.*")])
        if not path:
            return
        self.logo_path = path
        self.logo_path_var.set(path)
        self._load_logo(path)
        self._update_logo_preview()
        # Don't auto-save, let user click "Tallenna asetukset"

    def _update_logo_preview(self) -> None:
        """Update logo preview immediately after selection."""
        path = self.logo_path
        if not path or not hasattr(self, 'logo_preview_label'):
            return
        try:
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img is None:
                self.logo_preview_label.configure(image="", text="Logoa ei voitu ladata")
                return
            
            # Resize for preview (max 200x100)
            h, w = img.shape[:2]
            scale = min(200 / w, 100 / h, 1.0)
            new_w, new_h = int(w * scale), int(h * scale)
            resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            # Convert for Tkinter
            if resized.shape[2] == 4:
                resized_rgb = cv2.cvtColor(resized, cv2.COLOR_BGRA2RGBA)
            else:
                resized_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            
            preview_img = Image.fromarray(resized_rgb)
            preview_tk = ImageTk.PhotoImage(image=preview_img)
            
            self.logo_preview_label.configure(image=preview_tk, text="")
            self.logo_preview_label.image = preview_tk  # Keep reference
        except Exception:
            self.logger.warning("logo-preview-failed", exc_info=True)
            self.logo_preview_label.configure(image="", text="Esikatselun lataus epäonnistui")

    def _load_logo(self, path: Optional[str]) -> None:
        self.logo_bgra = None
        if not path:
            return
        try:
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img is None:
                self.logger.warning("logo-load-failed", extra={"path": path})
                return
            if img.shape[2] == 3:
                b, g, r = cv2.split(img)
                a = np.full_like(b, 255)
                img = cv2.merge((b, g, r, a))
            self.logo_bgra = img
        except Exception as e:
            self.logger.error("logo-load-error", exc_info=True)
            messagebox.showerror("Virhe", f"Logon lataus epäonnistui: {str(e)}")

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
        # Don't auto-save anymore, user must click "Tallenna asetukset"

    def _on_logo_alpha_change(self) -> None:
        """Called when logo alpha slider changes."""
        # Just update the display, don't auto-save
        pass

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
    
    def _pan(self, slot: int, dx: float, dy: float) -> None:
        """Pan camera view."""
        state = self.zoom_states[slot]
        state.pan(dx, dy)
    
    def _bind_hotkeys(self) -> None:
        """Bind keyboard shortcuts."""
        try:
            self.root.bind(f"<{self.hotkeys.refresh_live}>", lambda e: self.refresh_cameras_async())
            self.root.bind(f"<{self.hotkeys.zoom_in}>", lambda e: self._zoom_active_camera("in"))
            self.root.bind(f"<{self.hotkeys.zoom_out}>", lambda e: self._zoom_active_camera("out"))
            self.root.bind(f"<{self.hotkeys.pan_up}>", lambda e: self._pan_active_camera(0, -0.1))
            self.root.bind(f"<{self.hotkeys.pan_down}>", lambda e: self._pan_active_camera(0, 0.1))
            self.root.bind(f"<{self.hotkeys.pan_left}>", lambda e: self._pan_active_camera(-0.1, 0))
            self.root.bind(f"<{self.hotkeys.pan_right}>", lambda e: self._pan_active_camera(0.1, 0))
            # Mouse wheel zoom with Ctrl
            self.root.bind("<Control-MouseWheel>", self._on_mouse_wheel_zoom)
        except Exception as exc:
            self.logger.warning("hotkey-binding-failed", exc_info=exc)
    
    def _zoom_active_camera(self, direction: str) -> None:
        """Zoom the active camera."""
        slot = 0 if self.indices[0] is not None else (1 if self.indices[1] is not None else None)
        if slot is not None:
            self._update_zoom(slot, direction)
    
    def _pan_active_camera(self, dx: float, dy: float) -> None:
        """Pan the active camera."""
        slot = 0 if self.indices[0] is not None else (1 if self.indices[1] is not None else None)
        if slot is not None:
            self._pan(slot, dx, dy)
    
    def _on_mouse_wheel_zoom(self, event) -> None:
        """Handle Ctrl+MouseWheel zoom."""
        slot = 0 if self.indices[0] is not None else (1 if self.indices[1] is not None else None)
        if slot is not None:
            if event.delta > 0:
                self._update_zoom(slot, "in")
            else:
                self._update_zoom(slot, "out")
    
    def _attempt_reconnect(self, slot: int) -> None:
        """Attempt to reconnect a camera."""
        if self.indices[slot] is None:
            return
        try:
            self.reconnect_states[slot].record_attempt()
            self.start_camera(slot, self.indices[slot])
            if self.caps[slot] is not None:
                self.status_var.set(f"Kamera {slot + 1} yhdistetty uudelleen")
                self.logger.info("camera-reconnected", extra={"slot": slot})
        except Exception as exc:
            self.logger.warning("reconnect-failed", extra={"slot": slot}, exc_info=exc)
    
    def _tick_reconnect(self) -> None:
        """Periodic check for camera reconnection."""
        if self.root.winfo_exists():
            self.root.after(5000, self._tick_reconnect)
    
    def _on_autoreconnect_change(self) -> None:
        """Handle autoreconnect setting change."""
        enabled = self.autoreconnect_var.get()
        for state in self.reconnect_states:
            state.enabled = enabled
        self._save_settings()
    
    def _delete_selected_recording(self) -> None:
        """Delete selected recording(s) from list."""
        selection = self.events_view.selection()
        if not selection:
            messagebox.showinfo("Huom", "Valitse ensin tallenne(et).")
            return
        
        count = len(selection)
        if not messagebox.askyesno("Vahvista", f"Poistetaanko {count} tallenne(tta)?"):
            return
        
        for path_str in selection:
            try:
                path = Path(path_str)
                if path.exists():
                    path.unlink()
                # Remove from events list
                self.events = [e for e in self.events if e.path != path_str]
                self.logger.info("recording-deleted", extra={"path": path_str})
            except Exception as exc:
                self.logger.warning("delete-failed", extra={"path": path_str}, exc_info=exc)
                messagebox.showerror("Virhe", f"Poisto epäonnistui: {path_str}\n{exc}")
        
        self.refresh_events_view()
        self._update_usage_label()

    def _pan_camera(self, slot: int, dx: float, dy: float) -> None:
        """Pan a specific camera's view."""
        self.zoom_states[slot].pan(dx, dy)

    def save_snapshot(self) -> None:
        try:
            slot = 0 if self.indices[0] is not None else (1 if self.indices[1] is not None else None)
            if slot is None or self.last_frames_bgr[slot] is None:
                messagebox.showinfo("Huom", "Ei kuvaa tallennettavana.")
                return
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = self.record_dir / f"snapshot_cam{slot}_{ts}.png"
            success = cv2.imwrite(str(path), self.last_frames_bgr[slot])
            if not success:
                raise RuntimeError(f"Kuvan kirjoitus epäonnistui: {path}")
            messagebox.showinfo("Tallennettu", f"Kuvakaappaus tallennettu:\n{path}")
        except Exception as e:
            self.logger.error("snapshot-failed", exc_info=True)
            messagebox.showerror("Virhe", f"Kuvakaappauksen tallennus epäonnistui: {str(e)}")

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
    
    def _hotkey_zoom_in(self) -> None:
        """Hotkey handler for zoom in."""
        slot = 0 if self.indices[0] is not None else (1 if self.indices[1] is not None else None)
        if slot is not None:
            self._update_zoom(slot, "in")
    
    def _hotkey_zoom_out(self) -> None:
        """Hotkey handler for zoom out."""
        slot = 0 if self.indices[0] is not None else (1 if self.indices[1] is not None else None)
        if slot is not None:
            self._update_zoom(slot, "out")
    
    def _hotkey_reset_zoom(self) -> None:
        """Hotkey handler for reset zoom."""
        slot = 0 if self.indices[0] is not None else (1 if self.indices[1] is not None else None)
        if slot is not None:
            self._update_zoom(slot, "reset")
    
    def _hotkey_pan_left(self) -> None:
        """Hotkey handler for pan left."""
        self._pan_active_camera(-0.05, 0)
    
    def _hotkey_pan_right(self) -> None:
        """Hotkey handler for pan right."""
        self._pan_active_camera(0.05, 0)
    
    def _hotkey_pan_up(self) -> None:
        """Hotkey handler for pan up."""
        self._pan_active_camera(0, -0.05)
    
    def _hotkey_pan_down(self) -> None:
        """Hotkey handler for pan down."""
        self._pan_active_camera(0, 0.05)
    
    def _hotkey_toggle_recording(self) -> None:
        """Hotkey handler for toggle recording (placeholder)."""
        # Recording is controlled by motion detection, not manual toggle
        pass
    
    def _on_video_click(self, slot: int, event) -> None:
        """Handle mouse click on video feed."""
        # Store click position for potential dragging
        pass
    
    def _on_video_drag(self, slot: int, event) -> None:
        """Handle mouse drag on video feed."""
        # Could be used for pan/zoom with mouse in the future
        pass

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

    def _show_toast(self, message: str, error: bool = False) -> None:
        """Display a temporary toast notification."""
        if self._toast_window is not None:
            try:
                self._toast_window.destroy()
            except Exception:
                pass
        
        toast = tk.Toplevel(self.root)
        self._toast_window = toast
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        
        bg_color = "#8B0000" if error else "#2d5016"
        frame = tk.Frame(toast, bg=bg_color, padx=16, pady=12)
        frame.pack()
        
        label = tk.Label(frame, text=message, bg=bg_color, fg="white", font=("TkDefaultFont", 10))
        label.pack()
        
        # Position at bottom-right
        toast.update_idletasks()
        w = toast.winfo_width()
        h = toast.winfo_height()
        x = self.root.winfo_x() + self.root.winfo_width() - w - 20
        y = self.root.winfo_y() + self.root.winfo_height() - h - 60
        toast.geometry(f"+{x}+{y}")
        
        def hide_toast():
            try:
                toast.destroy()
            except Exception:
                pass
            self._toast_window = None
        
        self.root.after(3000, hide_toast)


__all__ = ["CameraApp"]
