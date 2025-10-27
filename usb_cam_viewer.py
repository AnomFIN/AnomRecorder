"""
AnomRecorder - USB Camera Viewer with Motion and Person Detection
A Windows-based camera surveillance system for USB cameras.
Features: Multi-camera support, motion/person detection, event recording, playback, screenshots.
"""

import cv2
import numpy as np
import os
import sys
import time
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk


class Config:
    """Configuration management for the camera system"""
    
    DEFAULT_CONFIG = {
        "camera_indices": [0],  # Camera device indices
        "resolution": [640, 480],  # Camera resolution
        "fps": 30,
        "motion_detection": True,
        "person_detection": True,
        "motion_threshold": 25,  # Motion sensitivity
        "motion_min_area": 500,  # Minimum area for motion detection
        "recording_duration": 10,  # Seconds to record after motion
        "max_storage_gb": 10,  # Maximum storage in GB
        "recordings_path": "recordings",
        "screenshots_path": "screenshots",
        "logo_path": "",  # Path to logo image (optional)
        "logo_position": "top-right",  # top-left, top-right, bottom-left, bottom-right
        "logo_scale": 0.15  # Scale factor for logo
    }
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults
                    config = self.DEFAULT_CONFIG.copy()
                    config.update(loaded)
                    return config
            except Exception as e:
                print(f"Error loading config: {e}, using defaults")
        return self.DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
        self.save_config()


class StorageManager:
    """Manage storage limits and cleanup old recordings"""
    
    def __init__(self, config):
        self.config = config
        self.recordings_path = config.get("recordings_path")
        os.makedirs(self.recordings_path, exist_ok=True)
    
    def get_directory_size(self):
        """Get total size of recordings directory in GB"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.recordings_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size / (1024 ** 3)  # Convert to GB
    
    def cleanup_old_recordings(self):
        """Remove oldest recordings if storage limit exceeded"""
        max_storage = self.config.get("max_storage_gb", 10)
        current_size = self.get_directory_size()
        
        if current_size > max_storage:
            # Get all video files with timestamps
            files = []
            for dirpath, dirnames, filenames in os.walk(self.recordings_path):
                for filename in filenames:
                    if filename.endswith(('.avi', '.mp4')):
                        filepath = os.path.join(dirpath, filename)
                        files.append((os.path.getmtime(filepath), filepath))
            
            # Sort by modification time (oldest first)
            files.sort()
            
            # Delete oldest files until under limit
            for mtime, filepath in files:
                if current_size <= max_storage * 0.9:  # Keep 10% buffer
                    break
                try:
                    file_size = os.path.getsize(filepath) / (1024 ** 3)
                    os.remove(filepath)
                    current_size -= file_size
                    print(f"Deleted old recording: {filepath}")
                except Exception as e:
                    print(f"Error deleting file {filepath}: {e}")


class CameraCapture:
    """Handle individual camera capture and processing"""
    
    def __init__(self, camera_index, config):
        self.camera_index = camera_index
        self.config = config
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.prev_frame = None
        self.motion_detected = False
        self.person_detected = False
        self.recording = False
        self.video_writer = None
        self.recording_start_time = None
        self.logo_overlay = None
        
        # Initialize HOG person detector
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        # Load logo if specified
        self.load_logo()
    
    def load_logo(self):
        """Load and prepare logo overlay"""
        logo_path = self.config.get("logo_path", "")
        if logo_path and os.path.exists(logo_path):
            try:
                logo = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
                if logo is not None:
                    scale = self.config.get("logo_scale", 0.15)
                    width = int(logo.shape[1] * scale)
                    height = int(logo.shape[0] * scale)
                    self.logo_overlay = cv2.resize(logo, (width, height))
            except Exception as e:
                print(f"Error loading logo: {e}")
    
    def open_camera(self):
        """Open camera device"""
        self.cap = cv2.VideoCapture(self.camera_index)
        if self.cap.isOpened():
            # Set resolution
            width, height = self.config.get("resolution", [640, 480])
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FPS, self.config.get("fps", 30))
            self.is_running = True
            return True
        return False
    
    def close_camera(self):
        """Close camera device"""
        self.is_running = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def detect_motion(self, frame):
        """Detect motion in frame"""
        if not self.config.get("motion_detection", True):
            return False
        
        # Convert to grayscale and blur
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Initialize previous frame
        if self.prev_frame is None:
            self.prev_frame = gray
            return False
        
        # Compute difference
        frame_delta = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(frame_delta, self.config.get("motion_threshold", 25), 
                              255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        # Check if any contour is large enough
        motion = False
        min_area = self.config.get("motion_min_area", 500)
        for contour in contours:
            if cv2.contourArea(contour) > min_area:
                motion = True
                # Draw rectangle around motion
                (x, y, w, h) = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        self.prev_frame = gray
        return motion
    
    def detect_person(self, frame):
        """Detect persons in frame using HOG-SVM"""
        if not self.config.get("person_detection", True):
            return False
        
        try:
            # Detect people
            (rects, weights) = self.hog.detectMultiScale(frame, 
                                                         winStride=(4, 4),
                                                         padding=(8, 8),
                                                         scale=1.05)
            
            # Draw rectangles around detected persons
            for (x, y, w, h) in rects:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            
            return len(rects) > 0
        except Exception as e:
            print(f"Person detection error: {e}")
            return False
    
    def apply_logo(self, frame):
        """Apply logo overlay to frame"""
        if self.logo_overlay is None:
            return frame
        
        try:
            logo = self.logo_overlay
            position = self.config.get("logo_position", "top-right")
            
            # Calculate position
            h, w = frame.shape[:2]
            lh, lw = logo.shape[:2]
            
            if position == "top-left":
                x, y = 10, 10
            elif position == "top-right":
                x, y = w - lw - 10, 10
            elif position == "bottom-left":
                x, y = 10, h - lh - 10
            else:  # bottom-right
                x, y = w - lw - 10, h - lh - 10
            
            # Apply logo with alpha channel if available
            if logo.shape[2] == 4:
                alpha = logo[:, :, 3] / 255.0
                for c in range(3):
                    frame[y:y+lh, x:x+lw, c] = (
                        alpha * logo[:, :, c] + 
                        (1 - alpha) * frame[y:y+lh, x:x+lw, c]
                    )
            else:
                frame[y:y+lh, x:x+lw] = logo[:, :, :3]
        except Exception as e:
            print(f"Logo overlay error: {e}")
        
        return frame
    
    def start_recording(self):
        """Start recording video"""
        if self.recording:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        recordings_path = self.config.get("recordings_path", "recordings")
        os.makedirs(recordings_path, exist_ok=True)
        
        filename = os.path.join(recordings_path, 
                               f"cam{self.camera_index}_{timestamp}.avi")
        
        # Get frame dimensions
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        fps = self.config.get("fps", 30)
        self.video_writer = cv2.VideoWriter(filename, fourcc, fps, (width, height))
        
        self.recording = True
        self.recording_start_time = time.time()
        print(f"Started recording: {filename}")
    
    def stop_recording(self):
        """Stop recording video"""
        if not self.recording:
            return
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        self.recording = False
        self.recording_start_time = None
        print("Stopped recording")
    
    def should_stop_recording(self):
        """Check if recording duration exceeded"""
        if not self.recording or not self.recording_start_time:
            return False
        
        duration = self.config.get("recording_duration", 10)
        elapsed = time.time() - self.recording_start_time
        return elapsed >= duration
    
    def capture_frame(self):
        """Capture and process a single frame"""
        if not self.cap or not self.is_running:
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        # Detect motion
        self.motion_detected = self.detect_motion(frame.copy())
        
        # Detect persons
        self.person_detected = self.detect_person(frame)
        
        # Start recording on motion or person detection
        if (self.motion_detected or self.person_detected) and not self.recording:
            self.start_recording()
        
        # Stop recording after duration
        if self.recording and self.should_stop_recording():
            self.stop_recording()
        
        # Write frame if recording
        if self.recording and self.video_writer:
            self.video_writer.write(frame)
        
        # Apply logo overlay
        frame = self.apply_logo(frame)
        
        # Add status text
        status_text = []
        if self.motion_detected:
            status_text.append("MOTION")
        if self.person_detected:
            status_text.append("PERSON")
        if self.recording:
            status_text.append("REC")
        
        if status_text:
            text = " | ".join(status_text)
            cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.7, (0, 0, 255), 2)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, frame.shape[0] - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        self.current_frame = frame
        return frame


class CameraViewer:
    """Main GUI application for camera viewing"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("AnomRecorder - USB Camera Viewer")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Load configuration
        self.config = Config()
        
        # Initialize storage manager
        self.storage_manager = StorageManager(self.config)
        
        # Initialize cameras
        self.cameras = []
        self.camera_labels = []
        self.is_running = False
        
        # Setup GUI
        self.setup_gui()
        
        # Start camera feeds
        self.start_cameras()
    
    def setup_gui(self):
        """Setup GUI components"""
        # Control panel
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Buttons
        self.start_btn = ttk.Button(control_frame, text="Start", 
                                    command=self.start_cameras)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="Stop", 
                                   command=self.stop_cameras)
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        self.screenshot_btn = ttk.Button(control_frame, text="Screenshot", 
                                        command=self.take_screenshot)
        self.screenshot_btn.grid(row=0, column=2, padx=5)
        
        self.playback_btn = ttk.Button(control_frame, text="Playback", 
                                       command=self.open_playback)
        self.playback_btn.grid(row=0, column=3, padx=5)
        
        self.settings_btn = ttk.Button(control_frame, text="Settings", 
                                       command=self.open_settings)
        self.settings_btn.grid(row=0, column=4, padx=5)
        
        # Status label
        self.status_label = ttk.Label(control_frame, text="Ready")
        self.status_label.grid(row=0, column=5, padx=20)
        
        # Camera display panels
        camera_indices = self.config.get("camera_indices", [0])
        num_cameras = len(camera_indices)
        
        for i, cam_idx in enumerate(camera_indices[:2]):  # Max 2 cameras
            label = tk.Label(self.root, bg="black")
            row = 1 + (i // 2)
            col = i % 2
            label.grid(row=row, column=col, padx=5, pady=5)
            self.camera_labels.append(label)
    
    def start_cameras(self):
        """Start all camera feeds"""
        if self.is_running:
            return
        
        camera_indices = self.config.get("camera_indices", [0])
        
        # Close existing cameras
        for cam in self.cameras:
            cam.close_camera()
        self.cameras = []
        
        # Open new cameras
        for cam_idx in camera_indices[:2]:  # Max 2 cameras
            camera = CameraCapture(cam_idx, self.config)
            if camera.open_camera():
                self.cameras.append(camera)
                print(f"Camera {cam_idx} opened successfully")
            else:
                messagebox.showerror("Error", f"Failed to open camera {cam_idx}")
        
        if self.cameras:
            self.is_running = True
            self.update_frames()
            self.status_label.config(text="Running")
    
    def stop_cameras(self):
        """Stop all camera feeds"""
        self.is_running = False
        for camera in self.cameras:
            camera.close_camera()
        self.status_label.config(text="Stopped")
    
    def update_frames(self):
        """Update camera frames in GUI"""
        if not self.is_running:
            return
        
        for i, camera in enumerate(self.cameras):
            if i >= len(self.camera_labels):
                break
            
            frame = camera.capture_frame()
            if frame is not None:
                # Convert to PIL Image and display
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.camera_labels[i].imgtk = imgtk
                self.camera_labels[i].configure(image=imgtk)
        
        # Check storage and cleanup if needed
        self.storage_manager.cleanup_old_recordings()
        
        # Schedule next update
        self.root.after(33, self.update_frames)  # ~30 FPS
    
    def take_screenshot(self):
        """Take screenshot from all cameras"""
        screenshots_path = self.config.get("screenshots_path", "screenshots")
        os.makedirs(screenshots_path, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, camera in enumerate(self.cameras):
            if camera.current_frame is not None:
                filename = os.path.join(screenshots_path, 
                                       f"cam{camera.camera_index}_{timestamp}.jpg")
                cv2.imwrite(filename, camera.current_frame)
                print(f"Screenshot saved: {filename}")
        
        messagebox.showinfo("Success", "Screenshots saved")
    
    def open_playback(self):
        """Open playback window"""
        PlaybackWindow(self.root, self.config)
    
    def open_settings(self):
        """Open settings window"""
        SettingsWindow(self.root, self.config, self.cameras)
    
    def on_closing(self):
        """Handle window closing"""
        self.stop_cameras()
        self.root.destroy()


class PlaybackWindow:
    """Window for playing back recorded videos"""
    
    def __init__(self, parent, config):
        self.config = config
        self.window = tk.Toplevel(parent)
        self.window.title("Playback")
        self.window.geometry("800x650")
        
        self.current_video = None
        self.cap = None
        self.is_playing = False
        
        self.setup_gui()
        self.load_recordings()
    
    def setup_gui(self):
        """Setup playback GUI"""
        # File list
        list_frame = ttk.Frame(self.window, padding="10")
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(list_frame, text="Recordings:").grid(row=0, column=0, sticky=tk.W)
        
        self.file_listbox = tk.Listbox(list_frame, width=50, height=10)
        self.file_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.file_listbox.bind('<<ListboxSelect>>', self.on_select)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, 
                                 command=self.file_listbox.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Control buttons
        btn_frame = ttk.Frame(self.window, padding="10")
        btn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.play_btn = ttk.Button(btn_frame, text="Play", command=self.play)
        self.play_btn.grid(row=0, column=0, padx=5)
        
        self.pause_btn = ttk.Button(btn_frame, text="Pause", command=self.pause)
        self.pause_btn.grid(row=0, column=1, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.stop)
        self.stop_btn.grid(row=0, column=2, padx=5)
        
        # Video display
        self.video_label = tk.Label(self.window, bg="black")
        self.video_label.grid(row=2, column=0, padx=10, pady=10)
    
    def load_recordings(self):
        """Load list of recorded videos"""
        recordings_path = self.config.get("recordings_path", "recordings")
        if not os.path.exists(recordings_path):
            return
        
        files = []
        for filename in os.listdir(recordings_path):
            if filename.endswith(('.avi', '.mp4')):
                filepath = os.path.join(recordings_path, filename)
                files.append((os.path.getmtime(filepath), filename, filepath))
        
        # Sort by modification time (newest first)
        files.sort(reverse=True)
        
        self.file_listbox.delete(0, tk.END)
        self.recordings = []
        for mtime, filename, filepath in files:
            timestamp = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            self.file_listbox.insert(tk.END, f"{timestamp} - {filename}")
            self.recordings.append(filepath)
    
    def on_select(self, event):
        """Handle file selection"""
        selection = self.file_listbox.curselection()
        if selection:
            self.current_video = self.recordings[selection[0]]
    
    def play(self):
        """Play selected video"""
        if not self.current_video:
            messagebox.showwarning("Warning", "Please select a video")
            return
        
        if self.cap:
            self.cap.release()
        
        self.cap = cv2.VideoCapture(self.current_video)
        self.is_playing = True
        self.play_frame()
    
    def play_frame(self):
        """Play next frame"""
        if not self.is_playing or not self.cap:
            return
        
        ret, frame = self.cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((640, 480))
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
            
            # Schedule next frame (30 FPS)
            self.window.after(33, self.play_frame)
        else:
            # Video ended
            self.stop()
    
    def pause(self):
        """Pause playback"""
        self.is_playing = False
    
    def stop(self):
        """Stop playback"""
        self.is_playing = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.video_label.configure(image='')


class SettingsWindow:
    """Window for configuring application settings"""
    
    def __init__(self, parent, config, cameras):
        self.config = config
        self.cameras = cameras
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("500x600")
        
        self.setup_gui()
    
    def setup_gui(self):
        """Setup settings GUI"""
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Camera settings
        cam_frame = ttk.Frame(notebook, padding="10")
        notebook.add(cam_frame, text="Camera")
        
        ttk.Label(cam_frame, text="Camera Indices (comma-separated):").grid(
            row=0, column=0, sticky=tk.W, pady=5)
        self.cam_indices = tk.StringVar(value=",".join(
            map(str, self.config.get("camera_indices", [0]))))
        ttk.Entry(cam_frame, textvariable=self.cam_indices, width=30).grid(
            row=0, column=1, pady=5)
        
        ttk.Label(cam_frame, text="Resolution (WxH):").grid(
            row=1, column=0, sticky=tk.W, pady=5)
        res = self.config.get("resolution", [640, 480])
        self.resolution = tk.StringVar(value=f"{res[0]}x{res[1]}")
        ttk.Entry(cam_frame, textvariable=self.resolution, width=30).grid(
            row=1, column=1, pady=5)
        
        ttk.Label(cam_frame, text="FPS:").grid(
            row=2, column=0, sticky=tk.W, pady=5)
        self.fps = tk.StringVar(value=str(self.config.get("fps", 30)))
        ttk.Entry(cam_frame, textvariable=self.fps, width=30).grid(
            row=2, column=1, pady=5)
        
        # Detection settings
        detect_frame = ttk.Frame(notebook, padding="10")
        notebook.add(detect_frame, text="Detection")
        
        self.motion_enabled = tk.BooleanVar(
            value=self.config.get("motion_detection", True))
        ttk.Checkbutton(detect_frame, text="Enable Motion Detection", 
                       variable=self.motion_enabled).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        self.person_enabled = tk.BooleanVar(
            value=self.config.get("person_detection", True))
        ttk.Checkbutton(detect_frame, text="Enable Person Detection", 
                       variable=self.person_enabled).grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Label(detect_frame, text="Motion Threshold:").grid(
            row=2, column=0, sticky=tk.W, pady=5)
        self.motion_threshold = tk.StringVar(
            value=str(self.config.get("motion_threshold", 25)))
        ttk.Entry(detect_frame, textvariable=self.motion_threshold, width=30).grid(
            row=2, column=1, pady=5)
        
        ttk.Label(detect_frame, text="Motion Min Area:").grid(
            row=3, column=0, sticky=tk.W, pady=5)
        self.motion_min_area = tk.StringVar(
            value=str(self.config.get("motion_min_area", 500)))
        ttk.Entry(detect_frame, textvariable=self.motion_min_area, width=30).grid(
            row=3, column=1, pady=5)
        
        # Recording settings
        rec_frame = ttk.Frame(notebook, padding="10")
        notebook.add(rec_frame, text="Recording")
        
        ttk.Label(rec_frame, text="Recording Duration (seconds):").grid(
            row=0, column=0, sticky=tk.W, pady=5)
        self.rec_duration = tk.StringVar(
            value=str(self.config.get("recording_duration", 10)))
        ttk.Entry(rec_frame, textvariable=self.rec_duration, width=30).grid(
            row=0, column=1, pady=5)
        
        ttk.Label(rec_frame, text="Max Storage (GB):").grid(
            row=1, column=0, sticky=tk.W, pady=5)
        self.max_storage = tk.StringVar(
            value=str(self.config.get("max_storage_gb", 10)))
        ttk.Entry(rec_frame, textvariable=self.max_storage, width=30).grid(
            row=1, column=1, pady=5)
        
        ttk.Label(rec_frame, text="Recordings Path:").grid(
            row=2, column=0, sticky=tk.W, pady=5)
        self.rec_path = tk.StringVar(
            value=self.config.get("recordings_path", "recordings"))
        ttk.Entry(rec_frame, textvariable=self.rec_path, width=30).grid(
            row=2, column=1, pady=5)
        
        # Logo settings
        logo_frame = ttk.Frame(notebook, padding="10")
        notebook.add(logo_frame, text="Logo")
        
        ttk.Label(logo_frame, text="Logo Path:").grid(
            row=0, column=0, sticky=tk.W, pady=5)
        self.logo_path = tk.StringVar(
            value=self.config.get("logo_path", ""))
        ttk.Entry(logo_frame, textvariable=self.logo_path, width=30).grid(
            row=0, column=1, pady=5)
        ttk.Button(logo_frame, text="Browse", 
                  command=self.browse_logo).grid(row=0, column=2, padx=5)
        
        ttk.Label(logo_frame, text="Logo Position:").grid(
            row=1, column=0, sticky=tk.W, pady=5)
        self.logo_position = tk.StringVar(
            value=self.config.get("logo_position", "top-right"))
        positions = ttk.Combobox(logo_frame, textvariable=self.logo_position, 
                                values=["top-left", "top-right", 
                                       "bottom-left", "bottom-right"],
                                state="readonly", width=27)
        positions.grid(row=1, column=1, pady=5)
        
        ttk.Label(logo_frame, text="Logo Scale:").grid(
            row=2, column=0, sticky=tk.W, pady=5)
        self.logo_scale = tk.StringVar(
            value=str(self.config.get("logo_scale", 0.15)))
        ttk.Entry(logo_frame, textvariable=self.logo_scale, width=30).grid(
            row=2, column=1, pady=5)
        
        # Save button
        btn_frame = ttk.Frame(self.window, padding="10")
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Save", command=self.save_settings).pack(
            side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(
            side=tk.RIGHT)
    
    def browse_logo(self):
        """Browse for logo file"""
        filename = filedialog.askopenfilename(
            title="Select Logo Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
        if filename:
            self.logo_path.set(filename)
    
    def save_settings(self):
        """Save settings to configuration"""
        try:
            # Parse and validate inputs
            cam_indices = [int(x.strip()) for x in self.cam_indices.get().split(',')]
            res = [int(x.strip()) for x in self.resolution.get().split('x')]
            
            # Update configuration
            self.config.set("camera_indices", cam_indices)
            self.config.set("resolution", res)
            self.config.set("fps", int(self.fps.get()))
            self.config.set("motion_detection", self.motion_enabled.get())
            self.config.set("person_detection", self.person_enabled.get())
            self.config.set("motion_threshold", int(self.motion_threshold.get()))
            self.config.set("motion_min_area", int(self.motion_min_area.get()))
            self.config.set("recording_duration", int(self.rec_duration.get()))
            self.config.set("max_storage_gb", float(self.max_storage.get()))
            self.config.set("recordings_path", self.rec_path.get())
            self.config.set("logo_path", self.logo_path.get())
            self.config.set("logo_position", self.logo_position.get())
            self.config.set("logo_scale", float(self.logo_scale.get()))
            
            # Reload logo for active cameras
            for camera in self.cameras:
                camera.load_logo()
            
            messagebox.showinfo("Success", "Settings saved successfully")
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid settings: {e}")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = CameraViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
