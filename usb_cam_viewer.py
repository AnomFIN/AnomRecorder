import os
import sys
import time
from typing import List, Tuple, Optional, Deque, Dict, Any
from collections import deque
from datetime import datetime
import base64
import numpy as np
import json

import cv2
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox


def list_cameras(max_indices: int = 10, probe_timeout: float = 1.0) -> List[Tuple[str, int]]:
    found = []
    for idx in range(max_indices):
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            continue
        start = time.time()
        ok = False
        while time.time() - start < probe_timeout:
            ok, _ = cap.read()
            if ok:
                break
            time.sleep(0.05)
        cap.release()
        if ok:
            found.append((f"usb-{len(found) + 1}", idx))
    return found


def _resource_candidate_roots() -> List[str]:
    roots = []
    try:
        roots.append(os.getcwd())
    except Exception:
        pass
    try:
        roots.append(os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        pass
    # When frozen with PyInstaller, prefer the executable directory
    if getattr(sys, "frozen", False):
        try:
            roots.append(os.path.dirname(sys.executable))
        except Exception:
            pass
    return list(dict.fromkeys([r for r in roots if r]))


def find_resource(rel_path: str) -> Optional[str]:
    for root in _resource_candidate_roots():
        p = os.path.join(root, rel_path)
        if os.path.exists(p):
            return p
    return None


class PersonDetector:
    def __init__(self):
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    @staticmethod
    def _sigmoid(x: float) -> float:
        try:
            import math

            return 1.0 / (1.0 + math.exp(-x))
        except Exception:
            return 0.5

    def detect(self, frame_bgr):
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        rects, weights = self.hog.detectMultiScale(
            gray,
            hitThreshold=0,
            winStride=(8, 8),
            padding=(8, 8),
            scale=1.05,
        )
        detections = []
        for (x, y, w, h), wgt in zip(rects, weights if weights is not None else []):
            # Map SVM score to [0, 1]
            conf = max(0.0, min(1.0, self._sigmoid(float(wgt))))
            detections.append(((x, y, w, h), conf))
        return detections


# Gender and identity recognition intentionally not implemented (safety policy)


class CameraApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Kamerajärjestelmä by AnomFIN")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Single or dual
        self.num_cams = tk.IntVar(value=1)

        # Caps and state for up to 2 cameras
        self.caps = [None, None]
        self.indices = [None, None]
        self.running = True
        self.frame_imgs = [None, None]

        # Detection components
        self.person_detector = PersonDetector()
        self.bgsubs = [cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=16, detectShadows=True),
                       cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=16, detectShadows=True)]
        self.enable_motion = tk.BooleanVar(value=True)
        self.enable_person = tk.BooleanVar(value=True)
        # No gender/identity features

        container = ttk.Frame(self.root, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        # Basic theme tweaks
        try:
            style = ttk.Style(self.root)
            style.theme_use('clam')
            style.configure('TNotebook.Tab', padding=(12, 6))
            style.configure('TLabel', font=('Segoe UI', 10))
            style.configure('TLabelframe.Label', font=('Segoe UI', 10, 'bold'))
            style.configure('TButton', font=('Segoe UI', 10))
        except Exception:
            pass

        # Notebook: Live and Events
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        live_tab = ttk.Frame(self.notebook)
        events_tab = ttk.Frame(self.notebook)
        settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(live_tab, text="Live")
        self.notebook.add(events_tab, text="Tapahtumat")
        self.notebook.add(settings_tab, text="Asetukset")

        top_bar = ttk.Frame(live_tab)
        top_bar.pack(fill=tk.X)

        ttk.Label(top_bar, text="Valitse kamera:").pack(side=tk.LEFT)

        self.camera_combo1 = ttk.Combobox(top_bar, width=12, state="readonly")
        self.camera_combo1.pack(side=tk.LEFT, padx=6)
        self.camera_combo1.bind("<<ComboboxSelected>>", lambda e: self.on_select_camera(0))

        self.camera_combo2 = ttk.Combobox(top_bar, width=12, state="readonly")
        self.camera_combo2.pack(side=tk.LEFT, padx=6)
        self.camera_combo2.bind("<<ComboboxSelected>>", lambda e: self.on_select_camera(1))

        ttk.Label(top_bar, text="Näkymä:").pack(side=tk.LEFT, padx=(12, 4))
        ttk.Radiobutton(top_bar, text="1", variable=self.num_cams, value=1, command=self.update_layout).pack(side=tk.LEFT)
        ttk.Radiobutton(top_bar, text="2", variable=self.num_cams, value=2, command=self.update_layout).pack(side=tk.LEFT)
        ttk.Radiobutton(top_bar, text="Tallenteet", variable=self.num_cams, value=3, command=self.select_recordings_view).pack(side=tk.LEFT)

        ttk.Button(top_bar, text="Päivitä lista", command=self.refresh_cameras).pack(side=tk.LEFT, padx=(12, 0))
        ttk.Button(top_bar, text="Kuvakaappaus", command=self.save_snapshot).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(top_bar, text="Sulje", command=self.on_close).pack(side=tk.RIGHT)

        opts_bar = ttk.Frame(live_tab)
        opts_bar.pack(fill=tk.X, pady=(8, 0))
        ttk.Checkbutton(opts_bar, text="Liikkeentunnistus", variable=self.enable_motion).pack(side=tk.LEFT)
        ttk.Checkbutton(opts_bar, text="Henkilötunnistus", variable=self.enable_person).pack(side=tk.LEFT, padx=(12, 0))

        self.video_area = ttk.Frame(live_tab)
        self.video_area.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.frame_label1 = ttk.Label(self.video_area)
        self.frame_label1.grid(row=0, column=0, sticky="nsew")

        self.frame_label2 = ttk.Label(self.video_area)
        self.frame_label2.grid(row=0, column=1, sticky="nsew")
        self.video_area.columnconfigure(0, weight=1)
        self.video_area.columnconfigure(1, weight=1)

        self.status_var = tk.StringVar(value="Valitse kamera listasta.")
        ttk.Label(live_tab, textvariable=self.status_var).pack(anchor=tk.W, pady=(8, 0))

        # Events tab
        events_top = ttk.Frame(events_tab)
        events_top.pack(fill=tk.X)
        ttk.Label(events_top, text="Tallenteet").pack(side=tk.LEFT)
        ttk.Button(events_top, text="Lisää merkintä", command=self.add_event_note).pack(side=tk.LEFT, padx=8)
        ttk.Button(events_top, text="Avaa kansio", command=self._open_recordings_folder).pack(side=tk.LEFT)

        events_body = ttk.Frame(events_tab)
        events_body.pack(fill=tk.BOTH, expand=True)
        cols = ("nimi", "aika", "kesto", "henkilot", "merkinnat")
        self.events_view = ttk.Treeview(events_body, columns=cols, show="headings", height=12)
        self.events_view.heading("nimi", text="Nimi")
        self.events_view.heading("aika", text="Alkuaika")
        self.events_view.heading("kesto", text="Kesto (s)")
        self.events_view.heading("henkilot", text="Henkilöitä")
        self.events_view.heading("merkinnat", text="Merkinnät")
        self.events_view.column("nimi", width=180)
        self.events_view.column("aika", width=160)
        self.events_view.column("kesto", width=80, anchor="center")
        self.events_view.column("henkilot", width=80, anchor="center")
        self.events_view.column("merkinnat", width=220)
        self.events_view.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        events_scroll = ttk.Scrollbar(events_body, orient=tk.VERTICAL, command=self.events_view.yview)
        self.events_view.configure(yscroll=events_scroll.set)
        events_scroll.pack(side=tk.LEFT, fill=tk.Y)

        playback_panel = ttk.Frame(events_tab)
        playback_panel.pack(fill=tk.BOTH, expand=True)
        self.playback_label = ttk.Label(playback_panel)
        self.playback_label.pack()
        self.playback_img = None
        self.events_view.bind("<<TreeviewSelect>>", self.on_select_event)

        # Initialize storage and branding BEFORE building Settings UI
        self.storage_limit_gb = tk.DoubleVar(value=5.0)
        self.usage_label_var = tk.StringVar(value="Käyttöaste: 0%, 0 MB / 5 GB")
        self.usage_progress = None
        self.logo_path = find_resource("logo.png")
        self.logo_alpha = tk.DoubleVar(value=0.25)
        self.logo_bgra = None
        # Motion trigger threshold (fraction 0.0..1.0), default ~5%
        self.motion_threshold = tk.DoubleVar(value=0.05)
        # Load persisted settings if present
        self._load_settings()
        # React to transparency slider changes
        try:
            self.logo_alpha.trace_add('write', lambda *args: self._save_settings())
            self.motion_threshold.trace_add('write', lambda *args: self._save_settings())
        except Exception:
            pass
        # Settings tab UI
        self._build_settings(settings_tab)

        self.refresh_cameras()
        self.update_layout()
        self.root.after(0, self.update_frames)

        # Recording/Events state
        self.record_dir = os.path.join(os.getcwd(), "recordings")
        os.makedirs(self.record_dir, exist_ok=True)
        self.recorder = [RollingRecorder(self.record_dir, cam_slot=0), RollingRecorder(self.record_dir, cam_slot=1)]
        self.event_counter = 0
        self.events: List[Dict[str, Any]] = []
        self.playback_vc: Optional[cv2.VideoCapture] = None
        self.playback_active = False
        self.playback_path: Optional[str] = None
        self.last_frames_bgr: List[Optional[np.ndarray]] = [None, None]

        # Storage and branding (continue)
        self.root.after(1000, self._tick_usage)
        self._load_logo(self.logo_path)
        if self.logo_bgra is None:
            # Fallback to built-in tiny placeholder (transparent PNG with simple bar)
            try:
                placeholder_b64 = (
                    "iVBORw0KGgoAAAANSUhEUgAAAEAAAAAUCAYAAAB0rOqMAAAACXBIWXMAAAsSAAALEgHS3X78"
                    "AAABFElEQVR4nO3XMWrCQBSF4Q9bS3gq1V1lQy5M5m0QyK5IYJgqQhpv8a6h3s1bqkQq1uPw0N"
                    "2kz1q3k5w0w5fS0vQ0eSg2H9q0o7xg3m0cQvZk3D0b9mS0TgZk2G0c0o7XvR7d2MCxv1bSpj8d"
                    "f4rQmWb5r2w7r/3qCk6M0EoYhQj5+Sg4gkFSmhLCkgi0lE0mDk9nYZk9g1gS9g8j4b3yHk3QxQ"
                    "rM7g4Q7vQh5Qv8h5fD9l7GfY4p9sJgWkqBqkqBqkqBqkqBqkqBqkqBqkqBqkqBqkqBqkqBqkqBq"
                    "kqBqkqBqkqBqkqBqkqBqkqBqkqBqkqBqkqD8wHqUo2m+qf2wAAAABJRU5ErkJggg=="
                )
                data = base64.b64decode(placeholder_b64)
                arr = np.frombuffer(data, dtype=np.uint8)
                img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
                self.logo_bgra = img
            except Exception:
                self.logo_bgra = None

    def refresh_cameras(self):
        cams = list_cameras()
        self.camera_list = cams
        labels = [name for name, _ in cams]
        self.camera_combo1["values"] = labels
        self.camera_combo2["values"] = labels
        if labels:
            if self.camera_combo1.current() == -1:
                self.camera_combo1.current(0)
                self.on_select_camera(0)
            if self.num_cams.get() == 2:
                if self.camera_combo2.current() == -1 and len(labels) > 1:
                    self.camera_combo2.current(1)
                    self.on_select_camera(1)
            self.status_var.set("Kamerat löydetty: " + ", ".join(labels))
        else:
            self.status_var.set("Kameraa ei löydy. Kytke USB-kamera ja paina 'Päivitä lista'.")
            self.stop_camera(0)
            self.stop_camera(1)

    def update_layout(self):
        if self.num_cams.get() == 1:
            self.frame_label2.grid_remove()
            # If second cam is open, keep it open but hidden? Simpler: stop it
            self.stop_camera(1)
        elif self.num_cams.get() == 2:
            self.frame_label2.grid()
            # Auto-select second cam if available
            if self.camera_combo2.current() == -1 and self.camera_combo2["values"]:
                if len(self.camera_combo2["values"]) > 1:
                    self.camera_combo2.current(1)
                    self.on_select_camera(1)
        elif self.num_cams.get() == 3:
            try:
                self.notebook.select(1)
            except Exception:
                pass

    def on_select_camera(self, slot: int):
        sel_combo = self.camera_combo1 if slot == 0 else self.camera_combo2
        sel = sel_combo.current()
        if sel == -1 or sel >= len(self.camera_list):
            self.stop_camera(slot)
            return
        _, index = self.camera_list[sel]
        self.start_camera(slot, index)

    def start_camera(self, slot: int, index: int):
        if self.indices[slot] == index and self.caps[slot] is not None:
            return
        self.stop_camera(slot)
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        if not cap.isOpened():
            self.status_var.set(f"Kamera {slot+1}: avaaminen epäonnistui.")
            try:
                cap.release()
            except Exception:
                pass
            return
        self.caps[slot] = cap
        self.indices[slot] = index
        self.status_var.set("Toistetaan livestreamia...")

    def stop_camera(self, slot: int):
        if self.caps[slot] is not None:
            try:
                self.caps[slot].release()
            except Exception:
                pass
        self.caps[slot] = None
        self.indices[slot] = None

    def _annotate(self, slot: int, frame_bgr):
        annotated = frame_bgr.copy()
        motion_level = 0.0
        if self.enable_motion.get() and self.bgsubs[slot] is not None:
            fg = self.bgsubs[slot].apply(frame_bgr)
            motion_level = float((fg > 0).sum()) / float(fg.size)
            if motion_level > 0.02:
                cv2.putText(
                    annotated,
                    f"Motion: {int(motion_level*100)}%",
                    (10, 24),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 165, 255),
                    2,
                    cv2.LINE_AA,
                )

        detections = []
        if self.enable_person.get():
            detections = self.person_detector.detect(annotated)
        for (x, y, w, h), conf in detections:
            color = (0, 255, 0) if conf >= 0.6 else (0, 200, 255)
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
            cv2.putText(
                annotated,
                f"Henkilö {int(conf*100)}%",
                (x, max(0, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
                cv2.LINE_AA,
            )
        # Timestamp overlay (local PC time)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(annotated, ts, (10, annotated.shape[0]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (240, 240, 240), 2, cv2.LINE_AA)
        # Logo overlay (if loaded)
        annotated = self._overlay_logo(annotated)
        return annotated

    def update_frames(self):
        if not self.running:
            return
        # If Events tab selected, update playback
        try:
            if self.notebook.index(self.notebook.select()) == 1:
                self.update_playback()
                self.root.after(33, self.update_frames)
                return
        except Exception:
            pass
        labels = [self.frame_label1, self.frame_label2]
        for slot in range(2):
            label = labels[slot]
            if slot == 1 and self.num_cams.get() == 1:
                # Clear second label image when hidden
                label.configure(image="")
                self.frame_imgs[slot] = None
                continue
            cap = self.caps[slot]
            if cap is None:
                continue
            ok, frame = cap.read()
            if not ok:
                continue
            annotated = self._annotate(slot, frame)
            # Motion trigger level for recording
            motion_trigger = False
            if self.enable_motion.get() and self.bgsubs[slot] is not None:
                fg = self.bgsubs[slot].apply(frame)
                lvl = float((fg > 0).sum()) / float(fg.size)
                motion_trigger = lvl > float(self.motion_threshold.get())
            person_count = len(self.person_detector.detect(annotated)) if self.enable_person.get() else 0

            new_event, finished_event = self.recorder[slot].update(annotated, motion_trigger, person_count)
            if new_event:
                self.event_counter += 1
                ev = {
                    "id": self.event_counter,
                    "name": f"Tallenne {self.event_counter}",
                    "path": new_event["path"],
                    "start": new_event["start"],
                    "end": None,
                    "duration": None,
                    "persons_max": 0,
                }
                self.events.append(ev)
                self.refresh_events_view()
            if finished_event:
                for ev in reversed(self.events):
                    if ev["path"] == finished_event["path"]:
                        ev["end"] = finished_event["end"]
                        ev["duration"] = finished_event["duration"]
                        ev["persons_max"] = finished_event.get("persons_max", ev.get("persons_max", 0))
                        break
                self.refresh_events_view()
                self._enforce_storage_limit()
                self._update_usage_label()

            # keep last frame for snapshots
            self.last_frames_bgr[slot] = annotated.copy()
            frame_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

            # downscale for UI performance
            max_w, max_h = (960, 540) if self.num_cams.get() == 1 else (640, 360)
            h, w, _ = frame_rgb.shape
            scale = min(max_w / w, max_h / h, 1.0)
            if scale < 1.0:
                frame_rgb = cv2.resize(frame_rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.frame_imgs[slot] = imgtk
            label.configure(image=imgtk)

        self.root.after(33, self.update_frames)  # ~30 FPS

    def on_close(self):
        self.running = False
        try:
            self._save_settings()
        except Exception:
            pass
        self.stop_camera(0)
        self.stop_camera(1)
        self.root.destroy()

    # ---------- Settings helpers ----------
    def _build_settings(self, tab: tk.Frame):
        outer = ttk.Frame(tab, padding=10)
        outer.pack(fill=tk.BOTH, expand=True)

        # Storage controls
        group = ttk.LabelFrame(outer, text="Tallennustila")
        group.pack(fill=tk.X, pady=6)
        ttk.Label(group, textvariable=self.usage_label_var).pack(anchor=tk.W, pady=(4, 4))
        self.usage_progress = ttk.Progressbar(group, orient=tk.HORIZONTAL, mode='determinate', length=400)
        self.usage_progress.pack(fill=tk.X)
        row = ttk.Frame(group)
        row.pack(fill=tk.X, pady=6)
        ttk.Label(row, text="Raja (GB):").pack(side=tk.LEFT)
        self.limit_entry = ttk.Entry(row, width=6, textvariable=self.storage_limit_gb)
        self.limit_entry.pack(side=tk.LEFT, padx=6)
        ttk.Button(row, text="Tallenna raja", command=self._save_limit).pack(side=tk.LEFT)
        ttk.Button(row, text="Tyhjennä tallenteet", command=self._clear_recordings).pack(side=tk.LEFT, padx=8)

        # Branding
        brand = ttk.LabelFrame(outer, text="Taustalogo")
        brand.pack(fill=tk.X, pady=6)
        brow = ttk.Frame(brand)
        brow.pack(fill=tk.X, pady=4)
        ttk.Label(brow, text="Valittu logo:").pack(side=tk.LEFT)
        self.logo_path_var = tk.StringVar(value=self.logo_path or "(ei valittua)")
        ttk.Label(brow, textvariable=self.logo_path_var).pack(side=tk.LEFT, padx=6)
        ttk.Button(brow, text="Valitse logo", command=self._choose_logo).pack(side=tk.LEFT)
        brow2 = ttk.Frame(brand)
        brow2.pack(fill=tk.X, pady=4)
        ttk.Label(brow2, text="Läpinäkyvyys").pack(side=tk.LEFT)
        ttk.Scale(brow2, from_=0.0, to=1.0, orient=tk.HORIZONTAL, variable=self.logo_alpha).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        # Motion sensitivity
        motion = ttk.LabelFrame(outer, text="Liikkeentunnistuksen herkkyys")
        motion.pack(fill=tk.X, pady=6)
        mrow = ttk.Frame(motion)
        mrow.pack(fill=tk.X, pady=4)
        ttk.Label(mrow, text="Raja (%):").pack(side=tk.LEFT)
        self.motion_thresh_label_var = tk.StringVar(value=f"{int(self.motion_threshold.get()*100)} %")
        ttk.Label(mrow, textvariable=self.motion_thresh_label_var).pack(side=tk.LEFT, padx=6)
        mrow2 = ttk.Frame(motion)
        mrow2.pack(fill=tk.X, pady=4)
        # Slider 0..30%
        def _on_motion_change(val=None):
            try:
                self.motion_thresh_label_var.set(f"{int(float(self.motion_threshold.get())*100)} %")
            except Exception:
                pass
        ttk.Scale(mrow2, from_=0.0, to=0.3, orient=tk.HORIZONTAL, variable=self.motion_threshold, command=lambda v: _on_motion_change()).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        # Footer
        ttk.Label(outer, text="Kamerajärjestelmä by AnomFIN", foreground="#666").pack(anchor=tk.E, pady=(12,0))

    def _save_limit(self):
        try:
            val = float(self.storage_limit_gb.get())
            if val <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Virhe", "Anna kelvollinen raja (GB > 0)")
            return
        self._enforce_storage_limit()
        self._update_usage_label()
        self._save_settings()

    def _clear_recordings(self):
        if not messagebox.askyesno("Vahvista", "Poistetaanko kaikki tallenteet? Tämä ei ole peruttavissa."):
            return
        for name in os.listdir(self.record_dir):
            p = os.path.join(self.record_dir, name)
            if os.path.isfile(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
        self._update_usage_label()
        self.refresh_events_view()

    def _choose_logo(self):
        path = filedialog.askopenfilename(title="Valitse logo", filetypes=[("Kuvat", "*.png;*.jpg;*.jpeg;*.bmp"), ("Kaikki", "*.*")])
        if not path:
            return
        self.logo_path = path
        self.logo_path_var.set(path)
        self._load_logo(path)
        self._save_settings()

    def _load_logo(self, path: Optional[str]):
        self.logo_bgra = None
        if not path:
            return
        try:
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img is None:
                return
            if img.shape[2] == 3:
                b, g, r = cv2.split(img)
                a = 255 * (img[...,0] == img[...,0])
                img = cv2.merge((b, g, r, a.astype('uint8')))
            self.logo_bgra = img
        except Exception:
            self.logo_bgra = None

    def _overlay_logo(self, frame_bgr):
        if self.logo_bgra is None:
            return frame_bgr
        overlay = self.logo_bgra
        h, w = frame_bgr.shape[:2]
        # scale logo to 20% width
        target_w = max(1, int(w * 0.2))
        scale = target_w / overlay.shape[1]
        new_size = (target_w, max(1, int(overlay.shape[0] * scale)))
        ov = cv2.resize(overlay, new_size, interpolation=cv2.INTER_AREA)
        oh, ow = ov.shape[:2]
        x = w - ow - 10
        y = 10
        if x < 0 or y < 0 or y+oh > h or x+ow > w:
            return frame_bgr
        roi = frame_bgr[y:y+oh, x:x+ow]
        alpha_logo = (ov[...,3].astype('float32')/255.0) * float(self.logo_alpha.get())
        alpha_bg = 1.0 - alpha_logo
        for c in range(3):
            roi[...,c] = (alpha_logo*ov[...,c].astype('float32') + alpha_bg*roi[...,c].astype('float32')).astype('uint8')
        frame_bgr[y:y+oh, x:x+ow] = roi
        return frame_bgr

    # ---------- Storage ----------
    def _dir_size_bytes(self, path: str) -> int:
        total = 0
        try:
            for name in os.listdir(path):
                p = os.path.join(path, name)
                if os.path.isfile(p):
                    try:
                        total += os.path.getsize(p)
                    except Exception:
                        pass
        except Exception:
            return 0
        return total

    def _human(self, b: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB"]
        v = float(b)
        i = 0
        while v >= 1024 and i < len(units)-1:
            v /= 1024
            i += 1
        return f"{v:.1f} {units[i]}" if i >= 2 else f"{int(v)} {units[i]}"

    def _update_usage_label(self):
        used = self._dir_size_bytes(self.record_dir)
        limit_b = int(max(0.0001, float(self.storage_limit_gb.get())) * (1024**3))
        pct = min(100, int((used/limit_b)*100)) if limit_b > 0 else 0
        self.usage_label_var.set(f"Käyttöaste: {pct}%, {self._human(used)} / {self._human(limit_b)}")
        if self.usage_progress is not None:
            self.usage_progress['value'] = pct

    def _tick_usage(self):
        self._update_usage_label()
        self.root.after(2000, self._tick_usage)

    def _enforce_storage_limit(self):
        limit_b = int(max(0.0001, float(self.storage_limit_gb.get())) * (1024**3))
        files = []
        try:
            for name in os.listdir(self.record_dir):
                p = os.path.join(self.record_dir, name)
                if os.path.isfile(p):
                    try:
                        files.append((os.path.getmtime(p), p, os.path.getsize(p)))
                    except Exception:
                        pass
        except Exception:
            return
        files.sort()  # oldest first
        total = sum(s for _, _, s in files)
        i = 0
        while total > limit_b and i < len(files):
            _, p, s = files[i]
            try:
                os.remove(p)
                total -= s
            except Exception:
                pass
            i += 1

    # ---------- Settings persistence ----------
    def _settings_path(self) -> str:
        return os.path.join(os.getcwd(), 'settings.json')

    def _load_settings(self):
        try:
            with open(self._settings_path(), 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return
        try:
            if 'storage_limit_gb' in data:
                self.storage_limit_gb.set(float(data['storage_limit_gb']))
        except Exception:
            pass
        try:
            if 'logo_path' in data and isinstance(data['logo_path'], str) and data['logo_path']:
                self.logo_path = data['logo_path']
        except Exception:
            pass
        try:
            if 'logo_alpha' in data:
                self.logo_alpha.set(float(data['logo_alpha']))
        except Exception:
            pass
        try:
            if 'motion_threshold' in data:
                self.motion_threshold.set(float(data['motion_threshold']))
        except Exception:
            pass

    def _save_settings(self):
        data = {
            'storage_limit_gb': float(self.storage_limit_gb.get()),
            'logo_path': self.logo_path or '',
            'logo_alpha': float(self.logo_alpha.get()),
            'motion_threshold': float(self.motion_threshold.get()),
        }
        try:
            with open(self._settings_path(), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def select_recordings_view(self):
        try:
            self.notebook.select(1)
        except Exception:
            pass

    def refresh_events_view(self):
        for i in self.events_view.get_children():
            self.events_view.delete(i)
        for ev in self.events:
            start_str = ev["start"].strftime("%Y-%m-%d %H:%M:%S") if ev.get("start") else ""
            dur = f"{ev['duration']:.1f}" if ev.get("duration") else ""
            persons = str(ev.get("persons_max", 0))
            note = ev.get("note", "")
            self.events_view.insert("", tk.END, iid=ev["path"], values=(ev["name"], start_str, dur, persons, note))

    def add_event_note(self):
        sel = self.events_view.selection()
        if not sel:
            messagebox.showinfo("Huom", "Valitse ensin tapahtuma listasta.")
            return
        path = sel[0]
        note = simpledialog.askstring("Lisää merkintä", "Kirjoita merkintä (esim. havainto):")
        if note is None:
            return
        for ev in self.events:
            if ev["path"] == path:
                ev["note"] = note.strip()
                break
        self.refresh_events_view()

    def on_select_event(self, event=None):
        sel = self.events_view.selection()
        if not sel:
            return
        path = sel[0]
        try:
            if self.playback_vc is not None:
                self.playback_vc.release()
        except Exception:
            pass
        self.playback_vc = cv2.VideoCapture(path)
        self.playback_active = True
        self.playback_path = path
        self.notebook.select(1)

    def update_playback(self):
        if not self.playback_active or self.playback_vc is None:
            return
        ok, frame = self.playback_vc.read()
        if not ok:
            self.playback_active = False
            return
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame_rgb.shape
        scale = min(960 / w, 540 / h, 1.0)
        if scale < 1.0:
            frame_rgb = cv2.resize(frame_rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        self.playback_img = imgtk
        self.playback_label.configure(image=imgtk)

    # ---------- Actions ----------
    def save_snapshot(self):
        # choose first active slot by default
        slot = 0 if self.indices[0] is not None else (1 if self.indices[1] is not None else None)
        if slot is None or self.last_frames_bgr[slot] is None:
            messagebox.showinfo("Huom", "Ei kuvaa tallennettavana.")
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.record_dir, f"snapshot_cam{slot}_{ts}.png")
        try:
            cv2.imwrite(path, self.last_frames_bgr[slot])
            messagebox.showinfo("Tallennettu", f"Kuvakaappaus tallennettu:\n{path}")
        except Exception as e:
            messagebox.showerror("Virhe", f"Kuvakaappauksen tallennus epäonnistui: {e}")

    def _open_recordings_folder(self):
        try:
            if sys.platform.startswith('win'):
                os.startfile(self.record_dir)
            elif sys.platform == 'darwin':
                os.system(f"open '{self.record_dir}'")
            else:
                os.system(f"xdg-open '{self.record_dir}' >/dev/null 2>&1 &")
        except Exception as e:
            messagebox.showerror("Virhe", f"Kansion avaaminen epäonnistui: {e}")


class RollingRecorder:
    def __init__(self, out_dir: str, cam_slot: int, pre_seconds: float = 3.0, post_seconds: float = 5.0, target_fps: int = 30):
        self.out_dir = out_dir
        self.cam_slot = cam_slot
        self.pre_seconds = pre_seconds
        self.post_seconds = post_seconds
        self.target_fps = target_fps
        self.prebuffer: Deque[Tuple[float, Any]] = deque(maxlen=int(pre_seconds * target_fps))
        self.recording = False
        self.writer: Optional[cv2.VideoWriter] = None
        self.last_motion_ts: Optional[float] = None
        self.start_ts: Optional[float] = None
        self.event_path: Optional[str] = None
        self.persons_max = 0

    def _writer_open(self, frame) -> cv2.VideoWriter:
        h, w = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        ts_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.out_dir, f"tallenne_cam{self.cam_slot}_{ts_name}.avi")
        writer = cv2.VideoWriter(path, fourcc, self.target_fps, (w, h))
        self.event_path = path
        return writer

    def update(self, frame_bgr, motion_trigger: bool, person_count: int):
        now = time.time()
        self.prebuffer.append((now, frame_bgr.copy()))

        new_event = None
        finished_event = None

        if motion_trigger and not self.recording:
            self.writer = self._writer_open(frame_bgr)
            cutoff = now - self.pre_seconds
            for ts, fr in list(self.prebuffer):
                if ts >= cutoff:
                    self.writer.write(fr)
            self.recording = True
            self.start_ts = now
            self.last_motion_ts = now
            self.persons_max = max(self.persons_max, person_count)
            new_event = {"path": self.event_path, "start": datetime.now()}

        if self.recording:
            self.writer.write(frame_bgr)
            if motion_trigger:
                self.last_motion_ts = now
                self.persons_max = max(self.persons_max, person_count)
            if self.last_motion_ts is not None and (now - self.last_motion_ts) >= self.post_seconds:
                try:
                    self.writer.release()
                except Exception:
                    pass
                dur = now - (self.start_ts or now)
                finished_event = {"path": self.event_path, "end": datetime.now(), "duration": dur, "persons_max": self.persons_max}
                self.recording = False
                self.writer = None
                self.last_motion_ts = None
                self.start_ts = None
                self.event_path = None
                self.persons_max = 0

        return new_event, finished_event


def main():
    root = tk.Tk()
    try:
        app = CameraApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Virhe", str(e))
        raise


if __name__ == "__main__":
    main()
