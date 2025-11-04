"""IP Camera configuration dialog.

Why this design:
- Provide both manual entry and automatic discovery in one dialog.
- Non-blocking network scan with progress feedback.
- Clear separation between manual and auto-discovery workflows.
"""

from __future__ import annotations

import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable

from ..services.ip_camera import CameraScanner, create_manual_camera, IPCamera
from .theme import PALETTE

# Innovation through simplicity.

LOGGER = logging.getLogger("anomrecorder.ui.ip_camera_dialog")


class IPCameraDialog:
    """Dialog for adding IP/WiFi cameras to AnomRecorder."""
    
    def __init__(self, parent: tk.Tk):
        self.parent = parent
        self.result: Optional[IPCamera] = None
        self.scanner = CameraScanner()
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Lisää IP/WiFi-kamera")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Apply theme
        self.dialog.configure(bg=PALETTE["bg"])
        
        self._build_ui()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
    def _build_ui(self) -> None:
        """Build the dialog UI with tabs for manual and auto-discovery."""
        main_frame = ttk.Frame(self.dialog, padding=16)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Manual entry tab
        manual_tab = ttk.Frame(notebook)
        notebook.add(manual_tab, text="Manuaalinen")
        self._build_manual_tab(manual_tab)
        
        # Auto-discovery tab
        auto_tab = ttk.Frame(notebook)
        notebook.add(auto_tab, text="Automaattinen haku")
        self._build_auto_tab(auto_tab)
        
        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(12, 0))
        
        ttk.Button(button_frame, text="Peruuta", command=self._on_cancel).pack(side=tk.RIGHT, padx=(8, 0))
        
    def _build_manual_tab(self, parent: ttk.Frame) -> None:
        """Build the manual IP entry tab."""
        # Info label
        info_label = ttk.Label(
            parent,
            text="Syötä kameran IP-osoite ja salasanatiedot:",
            wraplength=550
        )
        info_label.pack(anchor=tk.W, pady=(0, 12))
        
        # IP address
        ip_frame = ttk.Frame(parent)
        ip_frame.pack(fill=tk.X, pady=4)
        ttk.Label(ip_frame, text="IP-osoite:", width=15).pack(side=tk.LEFT)
        self.ip_entry = ttk.Entry(ip_frame)
        self.ip_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.ip_entry.insert(0, "192.168.1.100")
        
        # Port
        port_frame = ttk.Frame(parent)
        port_frame.pack(fill=tk.X, pady=4)
        ttk.Label(port_frame, text="Portti:", width=15).pack(side=tk.LEFT)
        self.port_entry = ttk.Entry(port_frame, width=10)
        self.port_entry.pack(side=tk.LEFT)
        self.port_entry.insert(0, "554")
        
        # Protocol
        protocol_frame = ttk.Frame(parent)
        protocol_frame.pack(fill=tk.X, pady=4)
        ttk.Label(protocol_frame, text="Protokolla:", width=15).pack(side=tk.LEFT)
        self.protocol_var = tk.StringVar(value="RTSP")
        ttk.Radiobutton(protocol_frame, text="RTSP", variable=self.protocol_var, value="RTSP").pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(protocol_frame, text="HTTP/MJPEG", variable=self.protocol_var, value="HTTP").pack(side=tk.LEFT, padx=4)
        
        # Username
        user_frame = ttk.Frame(parent)
        user_frame.pack(fill=tk.X, pady=4)
        ttk.Label(user_frame, text="Käyttäjänimi:", width=15).pack(side=tk.LEFT)
        self.username_entry = ttk.Entry(user_frame)
        self.username_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Password
        pass_frame = ttk.Frame(parent)
        pass_frame.pack(fill=tk.X, pady=4)
        ttk.Label(pass_frame, text="Salasana:", width=15).pack(side=tk.LEFT)
        self.password_entry = ttk.Entry(pass_frame, show="*")
        self.password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Optional path
        path_frame = ttk.Frame(parent)
        path_frame.pack(fill=tk.X, pady=4)
        ttk.Label(path_frame, text="Polku (opt.):", width=15).pack(side=tk.LEFT)
        self.path_entry = ttk.Entry(path_frame)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Hint label
        hint_label = ttk.Label(
            parent,
            text="Esim. RTSP: rtsp://192.168.1.100:554/stream1\n"
                 "HTTP: http://192.168.1.100:8080/video.mjpg",
            foreground=PALETTE["muted"],
            font=("TkDefaultFont", 9)
        )
        hint_label.pack(anchor=tk.W, pady=(12, 0))
        
        # Status label
        self.manual_status_var = tk.StringVar(value="")
        self.manual_status_label = ttk.Label(parent, textvariable=self.manual_status_var, foreground=PALETTE["accent"])
        self.manual_status_label.pack(anchor=tk.W, pady=(8, 0))
        
        # Test button
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(button_frame, text="Testaa yhteyttä", command=self._test_manual_connection).pack(side=tk.LEFT)
        self.add_manual_button = ttk.Button(button_frame, text="Lisää kamera", command=self._add_manual_camera, state=tk.DISABLED)
        self.add_manual_button.pack(side=tk.LEFT, padx=(8, 0))
        
    def _build_auto_tab(self, parent: ttk.Frame) -> None:
        """Build the automatic discovery tab."""
        # Info label
        info_label = ttk.Label(
            parent,
            text="Etsi automaattisesti yhteensopivia kameroita WiFi-verkosta.\n"
                 "Haku voi kestää useita minuutteja.",
            wraplength=550
        )
        info_label.pack(anchor=tk.W, pady=(0, 12))
        
        # Optional credentials for discovery
        cred_frame = ttk.LabelFrame(parent, text="Valinnaiset kirjautumistiedot", padding=8)
        cred_frame.pack(fill=tk.X, pady=(0, 12))
        
        user_frame = ttk.Frame(cred_frame)
        user_frame.pack(fill=tk.X, pady=2)
        ttk.Label(user_frame, text="Käyttäjänimi:", width=15).pack(side=tk.LEFT)
        self.scan_username_entry = ttk.Entry(user_frame)
        self.scan_username_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        pass_frame = ttk.Frame(cred_frame)
        pass_frame.pack(fill=tk.X, pady=2)
        ttk.Label(pass_frame, text="Salasana:", width=15).pack(side=tk.LEFT)
        self.scan_password_entry = ttk.Entry(pass_frame, show="*")
        self.scan_password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Scan controls
        scan_frame = ttk.Frame(parent)
        scan_frame.pack(fill=tk.X, pady=(0, 12))
        
        self.scan_button = ttk.Button(scan_frame, text="Aloita haku", command=self._start_scan)
        self.scan_button.pack(side=tk.LEFT)
        
        self.stop_scan_button = ttk.Button(scan_frame, text="Pysäytä", command=self._stop_scan, state=tk.DISABLED)
        self.stop_scan_button.pack(side=tk.LEFT, padx=(8, 0))
        
        # Progress
        self.progress_var = tk.StringVar(value="Valmis hakuun")
        ttk.Label(scan_frame, textvariable=self.progress_var).pack(side=tk.LEFT, padx=(16, 0))
        
        # Results list
        results_label = ttk.Label(parent, text="Löydetyt kamerat:")
        results_label.pack(anchor=tk.W)
        
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        
        # Treeview for results
        columns = ("ip", "port", "protocol")
        self.results_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", height=10)
        self.results_tree.heading("#0", text="Kamera")
        self.results_tree.heading("ip", text="IP")
        self.results_tree.heading("port", text="Portti")
        self.results_tree.heading("protocol", text="Protokolla")
        
        self.results_tree.column("#0", width=200)
        self.results_tree.column("ip", width=120)
        self.results_tree.column("port", width=60)
        self.results_tree.column("protocol", width=80)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add button
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(8, 0))
        self.add_auto_button = ttk.Button(button_frame, text="Lisää valittu kamera", command=self._add_auto_camera, state=tk.DISABLED)
        self.add_auto_button.pack(side=tk.LEFT)
        
    def _test_manual_connection(self) -> None:
        """Test manual IP camera connection."""
        ip = self.ip_entry.get().strip()
        port_str = self.port_entry.get().strip()
        protocol = self.protocol_var.get().lower()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        path = self.path_entry.get().strip()
        
        if not ip:
            messagebox.showerror("Virhe", "Anna IP-osoite")
            return
            
        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("Virhe", "Portin tulee olla numero")
            return
            
        self.manual_status_var.set("Testataan yhteyttä...")
        self.dialog.update()
        
        # Test connection in background
        def test_worker():
            camera = create_manual_camera(ip, port, protocol, username, password, path)
            
            # Update UI from main thread
            self.dialog.after(0, lambda: self._handle_manual_test_result(camera))
            
        threading.Thread(target=test_worker, daemon=True).start()
        
    def _handle_manual_test_result(self, camera: Optional[IPCamera]) -> None:
        """Handle result of manual connection test."""
        if camera:
            self.manual_status_var.set(f"✓ Yhteys onnistui: {camera.protocol.upper()}")
            self.add_manual_button.configure(state=tk.NORMAL)
            self.result = camera
        else:
            self.manual_status_var.set("✗ Yhteys epäonnistui. Tarkista asetukset.")
            self.add_manual_button.configure(state=tk.DISABLED)
            self.result = None
            
    def _add_manual_camera(self) -> None:
        """Add manually configured camera."""
        if self.result:
            self.dialog.destroy()
        else:
            messagebox.showwarning("Huomio", "Testaa yhteys ensin")
            
    def _start_scan(self) -> None:
        """Start automatic network scan."""
        username = self.scan_username_entry.get().strip()
        password = self.scan_password_entry.get()
        
        self.scan_button.configure(state=tk.DISABLED)
        self.stop_scan_button.configure(state=tk.NORMAL)
        self.add_auto_button.configure(state=tk.DISABLED)
        
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
        def progress_callback(current: int, total: int):
            """Update progress display."""
            percentage = int((current / total) * 100)
            msg = f"Skannataan: {current}/{total} ({percentage}%)"
            self.progress_var.set(msg)
            
            # Add any new cameras found
            found = self.scanner.get_found_cameras()
            existing_ips = set()
            for item in self.results_tree.get_children():
                values = self.results_tree.item(item)['values']
                if values:
                    existing_ips.add(values[0])
                    
            for camera in found:
                if camera.ip not in existing_ips:
                    self.results_tree.insert(
                        "", tk.END,
                        text=camera.name,
                        values=(camera.ip, camera.port, camera.protocol.upper())
                    )
                    existing_ips.add(camera.ip)
                    
            # Enable add button if cameras found
            if found:
                self.add_auto_button.configure(state=tk.NORMAL)
                
        self.scanner.start_scan(username, password, progress_callback)
        
        # Monitor scan completion
        self._check_scan_status()
        
    def _check_scan_status(self) -> None:
        """Check if scan is complete."""
        if not self.scanner.is_scanning:
            self.progress_var.set(f"Valmis. Löytyi {len(self.scanner.get_found_cameras())} kameraa.")
            self.scan_button.configure(state=tk.NORMAL)
            self.stop_scan_button.configure(state=tk.DISABLED)
        else:
            self.dialog.after(500, self._check_scan_status)
            
    def _stop_scan(self) -> None:
        """Stop ongoing scan."""
        self.scanner.stop_scan()
        self.scan_button.configure(state=tk.NORMAL)
        self.stop_scan_button.configure(state=tk.DISABLED)
        self.progress_var.set("Pysäytetty")
        
    def _add_auto_camera(self) -> None:
        """Add selected camera from scan results."""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("Huomio", "Valitse kamera listasta")
            return
            
        # Find selected camera
        item = selection[0]
        values = self.results_tree.item(item)['values']
        if not values:
            return
            
        ip = values[0]
        found_cameras = self.scanner.get_found_cameras()
        
        for camera in found_cameras:
            if camera.ip == ip:
                self.result = camera
                self.dialog.destroy()
                return
                
        messagebox.showerror("Virhe", "Kameraa ei löytynyt")
        
    def _on_cancel(self) -> None:
        """Cancel dialog."""
        self.scanner.stop_scan()
        self.result = None
        self.dialog.destroy()
        
    def show(self) -> Optional[IPCamera]:
        """Show dialog and return selected camera."""
        self.dialog.wait_window()
        return self.result


def show_ip_camera_dialog(parent: tk.Tk) -> Optional[IPCamera]:
    """Show IP camera configuration dialog.
    
    Args:
        parent: Parent Tk window
        
    Returns:
        IPCamera object if user adds a camera, None if cancelled
    """
    dialog = IPCameraDialog(parent)
    return dialog.show()


__all__ = ["show_ip_camera_dialog", "IPCameraDialog"]
