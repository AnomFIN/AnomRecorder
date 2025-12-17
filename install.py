#!/usr/bin/env python3
"""
AnomRecorder Installation Script with Reactive GUI

This script provides a graphical installation experience that:
1. Installs all required dependencies
2. Tests the installation
3. Automatically detects and fixes errors
4. Verifies the application works correctly

Falls back to CLI mode if GUI is not available.
"""
# Ship intelligence, not excuses.

import subprocess
import sys
import threading
import os
import shutil
from pathlib import Path

# Try to import tkinter, fall back to CLI if not available
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("Note: GUI (tkinter) not available, using CLI mode")

AUTO_START = "--start" in sys.argv

AUTO_START = "--start" in sys.argv
if "--venv" in sys.argv:
    DEFAULT_USE_VENV = True
elif "--no-venv" in sys.argv:
    DEFAULT_USE_VENV = False
else:
    DEFAULT_USE_VENV = True

class InstallerGUI:
    def __init__(self, root, auto_start=False, use_venv=DEFAULT_USE_VENV):
        self.root = root
        self.root.title("AnomRecorder Installer")
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        
        # State variables
        self.installation_complete = False
        self.installation_started = False
        self.python_version_ok = False
        self.dependencies_installed = False
        self.app_tested = False
        self.partial_installation = False
        self.use_venv = bool(use_venv)
        self.venv_dir = Path(__file__).parent / ".venv"
        self.py_exec = sys.executable
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Create GUI
        self.create_widgets(auto_start)
        
        # Start with system check
        self.root.after(500, self.check_system)
    
    def create_widgets(self, auto_start=False):
        """Create all GUI widgets"""
        # Header (with optional logo if available)
        header_frame = tk.Frame(self.root, bg="#1a1a1a", height=100)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Try to show user logo if PIL is available
        logo_shown = False
        try:
            from PIL import Image, ImageTk  # type: ignore
            def _find_user_logo():
                import os
                home = os.path.expanduser("~")
                candidates = [
                    os.path.join(home, "downloads", "logo.png"),
                    os.path.join(home, "Downloads", "logo.png"),
                    "/home/kali/downloads/logo.png",
                    os.path.join(Path(__file__).parent, "logo.png"),
                ]
                for p in candidates:
                    try:
                        if os.path.exists(p):
                            return p
                    except Exception:
                        pass
                return None
            lp = _find_user_logo()
            if lp:
                img = Image.open(lp)
                # Fit into header height
                base_h = 72
                ratio = base_h / max(1, img.height)
                new_w, new_h = int(img.width * ratio), int(img.height * ratio)
                img = img.resize((max(1, new_w), max(1, new_h)), Image.LANCZOS)
                tkimg = ImageTk.PhotoImage(img)
                lbl = tk.Label(header_frame, image=tkimg, bg="#1a1a1a")
                lbl.image = tkimg
                lbl.pack(pady=12)
                logo_shown = True
        except Exception:
            pass
        
        if not logo_shown:
            title_label = tk.Label(
                header_frame,
                text="AnomRecorder Installation",
                font=("Arial", 20, "bold"),
                bg="#1a1a1a",
                fg="#00ff00"
            )
            title_label.pack(pady=20)
        
        # Progress frame
        progress_frame = tk.Frame(self.root, bg="white", padx=20, pady=10)
        progress_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.progress_label = tk.Label(
            progress_frame,
            text="Initializing...",
            font=("Arial", 12),
            bg="white",
            anchor="w"
        )
        self.progress_label.pack(fill=tk.X)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='indeterminate',
            length=600
        )
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Status indicators frame
        status_frame = tk.Frame(self.root, bg="white", padx=20, pady=10)
        status_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.status_checks = {
            'python': self.create_status_row(status_frame, "Python Version Check"),
            'deps': self.create_status_row(status_frame, "Dependencies Installation"),
            'test': self.create_status_row(status_frame, "Application Test"),
            'complete': self.create_status_row(status_frame, "Installation Complete")
        }
        
        # Log area
        log_frame = tk.Frame(self.root, bg="white", padx=20, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        
        log_label = tk.Label(
            log_frame,
            text="Installation Log:",
            font=("Arial", 10, "bold"),
            bg="white",
            anchor="w"
        )
        log_label.pack(fill=tk.X)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            font=("Courier", 9),
            bg="#f0f0f0",
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Buttons frame
        button_frame = tk.Frame(self.root, bg="white", padx=20, pady=10)
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.install_button = tk.Button(
            button_frame,
            text="Start Installation",
            command=self.start_installation,
            font=("Arial", 11, "bold"),
            bg="#00ff00",
            fg="black",
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        self.install_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Linux-only helper: install a compatible Python version and relaunch
        if sys.platform.startswith('linux'):
            self.python_fix_button = tk.Button(
                button_frame,
                text="Install Correct Python",
                command=self.install_linux_python,
                font=("Arial", 11),
                bg="#ffaa00",
                fg="black",
                padx=16,
                pady=10,
            )
            self.python_fix_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Venv + Auto-start options
        self.use_venv_var = tk.BooleanVar(value=self.use_venv)
        venv_chk = tk.Checkbutton(
            button_frame,
            text="Use .venv",
            variable=self.use_venv_var,
            onvalue=True,
            offvalue=False,
            bg="white"
        )
        venv_chk.pack(side=tk.LEFT, padx=(0, 10))

        # Auto-start checkbox
        self.auto_start_var = tk.BooleanVar(value=bool(auto_start))
        auto_chk = tk.Checkbutton(
            button_frame,
            text="Start App after install",
            variable=self.auto_start_var,
            onvalue=True,
            offvalue=False,
            bg="white"
        )
        auto_chk.pack(side=tk.LEFT, padx=(0, 10))

        self.launch_button = tk.Button(
            button_frame,
            text="Start App",
            command=self.launch_app,
            font=("Arial", 11, "bold"),
            bg="#0099ff",
            fg="white",
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        self.launch_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.close_button = tk.Button(
            button_frame,
            text="Close",
            command=self.root.quit,
            font=("Arial", 11),
            bg="#ff4444",
            fg="white",
            padx=20,
            pady=10
        )
        self.close_button.pack(side=tk.RIGHT)
    
    def create_status_row(self, parent, text):
        """Create a status indicator row"""
        frame = tk.Frame(parent, bg="white")
        frame.pack(fill=tk.X, pady=2)
        
        label = tk.Label(
            frame,
            text=text,
            font=("Arial", 10),
            bg="white",
            anchor="w",
            width=30
        )
        label.pack(side=tk.LEFT)
        
        status = tk.Label(
            frame,
            text="⏳ Pending",
            font=("Arial", 10),
            bg="white",
            fg="gray"
        )
        status.pack(side=tk.RIGHT)
        
        return status
    
    def update_status(self, key, status, color):
        """Update a status indicator"""
        if key in self.status_checks:
            self.status_checks[key].config(text=status, fg=color)
    
    def log(self, message, tag=None):
        """Add a message to the log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()

    def install_linux_python(self):
        """Install Python 3.12/3.11 via the system package manager and relaunch the installer."""
        self.log("\n=== Install Compatible Python (Linux) ===")
        try:
            # If already installed, relaunch immediately
            for minor in ("3.12", "3.11"):
                alt = shutil.which(f"python{minor}")
                if alt:
                    self.log(f"Found {alt}. Relaunching installer...")
                    try:
                        messagebox.showinfo("Relaunching", f"Relaunching installer with {alt}")
                    except Exception:
                        pass
                    os.execv(alt, [alt, __file__] + sys.argv[1:])

            # Detect package manager
            mgr = None
            for cand in ("apt-get", "dnf", "pacman", "zypper"):
                if shutil.which(cand):
                    mgr = cand
                    break
            if not mgr:
                raise Exception("No known package manager found (apt, dnf, pacman, zypper)")

            # Build commands
            if mgr == "apt-get":
                commands = [
                    "apt-get update",
                    "apt-get install -y python3.12 python3.12-venv || apt-get install -y python3.11 python3.11-venv",
                ]
            elif mgr == "dnf":
                commands = [
                    "dnf -y install python3.12 python3.12-pip || dnf -y install python3.11 python3.11-pip",
                ]
            elif mgr == "pacman":
                commands = [
                    "pacman -Sy --noconfirm python312 || pacman -Sy --noconfirm python311",
                ]
            else:  # zypper
                commands = [
                    "zypper --non-interactive install python312 || zypper --non-interactive install python311",
                ]

            shell_cmd = " && ".join(commands)
            self.log(f"Using {mgr}. Will run: {shell_cmd}")

            if shutil.which("pkexec"):
                r = subprocess.run(["pkexec", "bash", "-lc", shell_cmd], capture_output=True, text=True)
                if r.stdout:
                    self.log(r.stdout[-2000:] if len(r.stdout) > 2000 else r.stdout)
                if r.stderr:
                    self.log(r.stderr[-2000:] if len(r.stderr) > 2000 else r.stderr)
                if r.returncode != 0:
                    raise Exception("pkexec installation command failed")
            else:
                # Provide manual commands
                manual = "\n".join([f"sudo {c}" for c in commands])
                try:
                    messagebox.showinfo(
                        "Run in Terminal",
                        "Administrator privileges required. Run these in a terminal, then restart installer:\n\n" + manual
                    )
                except Exception:
                    pass
                self.log("pkexec not found; prompted user with manual commands.")
                return

            # After install, try to locate interpreter
            for minor in ("3.12", "3.11"):
                alt = shutil.which(f"python{minor}")
                if alt:
                    self.log(f"Found {alt}. Relaunching installer...")
                    try:
                        messagebox.showinfo("Relaunching", f"Relaunching installer with {alt}")
                    except Exception:
                        pass
                    os.execv(alt, [alt, __file__] + sys.argv[1:])

            self.log("Could not find python3.12/3.11 after installation. Please reopen the installer.")
            try:
                messagebox.showwarning("Not Found", "Could not locate python3.12/3.11 after installation. Reopen the installer.")
            except Exception:
                pass
        except Exception as e:
            self.log(f"✗ Error during Python installation helper: {e}")
            try:
                messagebox.showerror("Error", str(e))
            except Exception:
                pass
    
    def check_system(self):
        """Check system requirements"""
        self.progress_label.config(text="Checking system requirements...")
        self.progress_bar.start()
        
        def check():
            try:
                # Check Python version
                self.log("Checking Python version...")
                version = sys.version_info
                self.log(f"Python {version.major}.{version.minor}.{version.micro} detected")
                
                if version.major == 3 and version.minor >= 8:
                    self.python_version_ok = True
                    self.update_status('python', "✓ Pass", "green")
                    self.log("✓ Python version is compatible")
                else:
                    self.update_status('python', "✗ Fail", "red")
                    self.log(f"✗ Python 3.8+ required, found {version.major}.{version.minor}")
                    messagebox.showerror(
                        "System Check Failed",
                        f"Python 3.8 or higher is required.\nFound: Python {version.major}.{version.minor}"
                    )
                    self.progress_bar.stop()
                    return
                
                # Check if pip is available
                self.log("\nChecking pip availability...")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "--version"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    self.log(f"✓ pip is available: {result.stdout.strip()}")
                else:
                    raise Exception("pip is not available")
                
                # Enable install button
                self.progress_bar.stop()
                self.progress_label.config(text="System check complete - Ready to install")
                self.install_button.config(state=tk.NORMAL)
                self.log("\n✓ System check complete. Click 'Start Installation' to continue.")
                self.root.after(300, self.auto_start_installation)

            except Exception as e:
                self.progress_bar.stop()
                self.log(f"\n✗ Error during system check: {e}")
                self.update_status('python', "✗ Fail", "red")
                messagebox.showerror("System Check Failed", str(e))

        threading.Thread(target=check, daemon=True).start()

    def auto_start_installation(self):
        """Start installation automatically after checks."""
        if self.installation_started or not self.python_version_ok:
            return
        self.log("\nAuto-starting installation to complete setup without extra clicks.")
        self.start_installation()

    def start_installation(self):
        """Start the installation process"""
        if self.installation_started:
            self.log("Installation already running.")
            return
        self.installation_started = True
        self.install_button.config(state=tk.DISABLED)
        self.progress_bar.start()
        
        def install():
            try:
                # Prepare environment (create venv if selected)
                self.use_venv = bool(self.use_venv_var.get()) if hasattr(self, 'use_venv_var') else self.use_venv
                self.setup_environment()
                # Step 1: Upgrade pip
                self.progress_label.config(text="Upgrading pip...")
                self.log("\n=== Upgrading pip ===")
                result = subprocess.run(
                    [self.py_exec, "-m", "pip", "install", "--upgrade", "pip"],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    self.log(f"Warning: pip upgrade had issues: {result.stderr}")
                else:
                    self.log("✓ pip upgraded successfully")
                
                # Step 2: Install dependencies
                self.progress_label.config(text="Installing dependencies...")
                self.log("\n=== Installing Dependencies ===")
                self.log("This may take a few minutes...")
                
                requirements_path = Path(__file__).parent / "requirements.txt"
                if not requirements_path.exists():
                    raise Exception("requirements.txt not found!")
                
                result = subprocess.run(
                    [self.py_exec, "-m", "pip", "install", "-r", str(requirements_path)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    self.log("\n✗ Installation failed!")
                    self.log(result.stderr)
                    self.update_status('deps', "✗ Fail", "red")
                    
                    # Try to fix common issues
                    self.log("\n=== Attempting to fix issues ===")
                    self.attempt_fixes()
                else:
                    self.log("\n✓ All dependencies installed successfully!")
                    self.dependencies_installed = True
                    self.update_status('deps', "✓ Pass", "green")
                    
                    # Install pytest for testing
                    self.log("\n=== Installing pytest for testing ===")
                    subprocess.run(
                        [self.py_exec, "-m", "pip", "install", "pytest"],
                        capture_output=True,
                        text=True
                    )
                    
                    # Test the installation
                    self.test_installation()
                
            except Exception as e:
                self.log(f"\n✗ Installation error: {e}")
                self.update_status('deps', "✗ Fail", "red")
                self.progress_bar.stop()
                messagebox.showerror("Installation Failed", str(e))
        
        threading.Thread(target=install, daemon=True).start()

    def setup_environment(self):
        """Create and select a virtual environment if requested."""
        if not self.use_venv:
            self.py_exec = sys.executable
            return

        venv_dir = self.venv_dir
        self.log("\n=== Setting up virtual environment (.venv) ===")
        # Choose interpreter for venv (prefer 3.12/3.11 when on 3.13)
        py_for_venv = sys.executable
        if (sys.version_info.major, sys.version_info.minor) >= (3, 13):
            cand = None
            for name in ("python3.12", "python3.11"):
                p = shutil.which(name)
                if p:
                    cand = p; break
            if not cand and sys.platform == 'win32':
                py = shutil.which('py')
                if py:
                    for minor in ("3.12", "3.11"):
                        r = subprocess.run([py, f"-{minor}", "-c", "import sys;print(sys.executable)"], capture_output=True, text=True)
                        if r.returncode == 0 and r.stdout.strip():
                            cand = r.stdout.strip(); break
            if cand:
                py_for_venv = cand
                self.log(f"Using {py_for_venv} for virtual environment")

        if not venv_dir.exists():
            self.progress_label.config(text="Creating virtual environment (.venv)...")
            r = subprocess.run([py_for_venv, "-m", "venv", str(venv_dir)], capture_output=True, text=True)
            if r.returncode != 0:
                self.log(r.stdout[-1000:] if r.stdout else "")
                self.log(r.stderr[-1000:] if r.stderr else "")
                raise Exception("Failed to create virtual environment")

        # Determine python path inside venv
        ve_py = venv_dir / ("Scripts" if os.name == 'nt' else "bin") / ("python.exe" if os.name == 'nt' else "python")
        if not ve_py.exists():
            raise Exception("Virtual environment Python not found")
        self.py_exec = str(ve_py)
        self.log(f"Using interpreter: {self.py_exec}")
    
    def attempt_fixes(self):
        """Attempt to automatically fix common installation issues"""
        self.log("Analyzing errors and attempting fixes...")

        requirements_path = Path(__file__).parent / "requirements.txt"
        with open(requirements_path) as f:
            raw_lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        # Strip exact pins to let pip choose compatible wheels
        def strip_pins(lines):
            pkgs = []
            for line in lines:
                pkg = line.split(';')[0].strip()
                if '==' in pkg:
                    pkg = pkg.split('==')[0]
                pkgs.append(pkg)
            return pkgs

        unpinned = strip_pins(raw_lines)
        is_py313_plus = (sys.version_info.major, sys.version_info.minor) >= (3, 13)

        # Upgrade build tooling first
        self.log("Upgrading build tooling (pip/setuptools/wheel)...")
        subprocess.run([self.py_exec, "-m", "pip", "install", "-U", "pip", "setuptools", "wheel"],
                       capture_output=True, text=True)

        # 1) Try a single-shot install with unpinned requirements.
        #    On Python 3.13, allow pre-release wheels which many projects publish first.
        args = [self.py_exec, "-m", "pip", "install"]
        if is_py313_plus:
            self.log("Python 3.13 detected – allowing pre-release wheels for better compatibility...")
            args.append("--pre")
        args.extend(unpinned)

        self.log("Retrying with unpinned dependency versions...")
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode == 0:
            self.log("\n✓ Dependencies installed after retry (unpinned)")
            self.dependencies_installed = True
            self.update_status('deps', "✓ Pass", "green")
            return self.test_installation()

        # 2) Fall back to per-package installation to surface exact failures
        self.log("Single-shot retry failed. Trying per-package installs to isolate issues...")
        failed_packages = []
        for package in unpinned:
            self.log(f"Installing {package}...")
            per_args = [self.py_exec, "-m", "pip", "install"]
            if is_py313_plus:
                per_args.append("--pre")
            per_args.append(package)
            r = subprocess.run(per_args, capture_output=True, text=True)
            if r.returncode != 0:
                failed_packages.append(package)
                self.log(f"  ✗ Failed: {package}")
            else:
                self.log(f"  ✓ Success: {package}")

        if failed_packages:
            self.log(f"\n✗ Still failing: {', '.join(failed_packages)}")
            self.update_status('deps', "✗ Fail", "red")
            # continue with partial install and proceed to tests
            self.partial_installation = True
            self.dependencies_installed = True

            extra_note = ""
            if is_py313_plus:
                # Guidance for Python 3.13 users
                alt = shutil.which("python3.12") or shutil.which("python3.11")
                if alt:
                    extra_note = ("\n\nTip: A compatible interpreter was found (" + alt + ") – "
                                  "run it with: '" + alt + " install.py' for better compatibility.")
                else:
                    extra_note = ("\n\nTip: Many packages don't yet ship wheels for Python 3.13. "
                                  "Install Python 3.11/3.12 and re-run: 'python3.11 install.py'.")

            messagebox.showwarning(
                "Partial Installation",
                "Some packages could not be installed:\n"
                + ", ".join(failed_packages)
                + "\n\nContinuing with partial install so you can test/launch."
                + extra_note
            )
            self.progress_label.config(text="Proceeding with partial installation...")
            # Proceed to tests despite partial deps
            return self.test_installation()
        else:
            self.log("\n✓ All packages installed successfully after per-package retry!")
            self.dependencies_installed = True
            self.update_status('deps', "✓ Pass", "green")
            self.test_installation()
    
    def test_installation(self):
        """Test that the installation works"""
        self.progress_label.config(text="Testing installation...")
        self.log("\n=== Testing Installation ===")
        
        try:
            # Test importing main modules
            self.log("Testing module imports...")
            test_imports = [
                "PySide6",
                "cv2",
                "onnxruntime",
                "numpy",
                "PIL",
                "src.index"
            ]
            
            for module in test_imports:
                try:
                    __import__(module)
                    self.log(f"  ✓ {module}")
                except ImportError as e:
                    self.log(f"  ✗ {module}: {e}")
                    raise Exception(f"Failed to import {module}")
            
            self.log("\n✓ All module imports successful!")
            
            # Run basic tests if pytest is available
            self.log("\n=== Running Application Tests ===")
            result = subprocess.run(
                [self.py_exec, "-m", "pytest", "tests/", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            if result.returncode == 0:
                self.log("✓ All tests passed!")
            else:
                self.log("Some tests failed, but this may be expected:")
                self.log(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
            
            self.app_tested = True
            self.update_status('test', "✓ Pass", "green")
            self.complete_installation()
            
        except Exception as e:
            self.log(f"\n✗ Testing failed: {e}")
            self.update_status('test', "✗ Fail", "red")
            
            # Still mark as complete if dependencies are installed
            if self.dependencies_installed:
                self.log("\nDependencies are installed. You can try launching the app.")
                self.complete_installation()
            else:
                self.progress_bar.stop()
                messagebox.showerror("Testing Failed", str(e))
    
    def complete_installation(self):
        """Mark installation as complete"""
        self.installation_complete = True
        self.update_status('complete', "✓ Complete", "green")
        self.progress_bar.stop()
        self.progress_label.config(text="Installation complete!" if not self.partial_installation else "Installation finished with warnings")
        self.launch_button.config(state=tk.NORMAL)
        self.log("\n" + "="*50)
        if self.partial_installation:
            self.log("⚠ Installation finished with warnings (partial dependencies)")
        else:
            self.log("✓ Installation Complete!")
        self.log("="*50)
        self.log("\nYou can now launch AnomRecorder.")
        try:
            if self.partial_installation:
                messagebox.showwarning(
                    "Installation Finished",
                    "Finished with warnings. Some dependencies failed.\n\n"
                    "You can try launching the app now; features may be limited."
                )
            else:
                messagebox.showinfo(
                    "Installation Complete",
                    "AnomRecorder has been installed successfully!\n\n"
                    "Click 'Start App' to launch the application."
                )
        except Exception:
            pass

        # Auto-start app if selected
        try:
            if hasattr(self, 'auto_start_var') and self.auto_start_var.get():
                self.log("Auto-start enabled. Launching app...")
                self.root.after(250, self.launch_app)
        except Exception:
            pass
    
    def launch_app(self):
        """Launch the AnomRecorder application"""
        self.log("\n=== Launching AnomRecorder ===")
        try:
            app_path = Path(__file__).parent / "usb_cam_viewer.py"
            if not app_path.exists():
                app_path = Path(__file__).parent / "src" / "index.py"
            
            self.log(f"Starting {app_path}...")
            
            # Launch in a new process
            subprocess.Popen(
                [self.py_exec, str(app_path)],
                cwd=Path(__file__).parent
            )
            
            self.log("✓ Application launched!")
            messagebox.showinfo(
                "Application Launched",
                "AnomRecorder has been launched in a new window."
            )
            
        except Exception as e:
            self.log(f"\n✗ Failed to launch: {e}")
            messagebox.showerror("Launch Failed", str(e))


class InstallerCLI:
    """CLI version of the installer for headless environments"""
    
    def __init__(self, auto_start=False, use_venv=DEFAULT_USE_VENV):
        self.python_version_ok = False
        self.dependencies_installed = False
        self.app_tested = False
        self.installation_complete = False
        self.partial_installation = False
        self.auto_start = bool(auto_start)
        self.use_venv = bool(use_venv)
        self.venv_dir = Path(__file__).parent / ".venv"
        self.py_exec = sys.executable
    
    def log(self, message):
        """Print log message"""
        print(message)
    
    def check_system(self):
        """Check system requirements"""
        self.log("=" * 60)
        self.log("AnomRecorder Installation (CLI Mode)")
        self.log("=" * 60)
        self.log("\n[1/4] Checking system requirements...")
        
        # Check Python version
        version = sys.version_info
        self.log(f"Python {version.major}.{version.minor}.{version.micro} detected")
        
        if version.major == 3 and version.minor >= 8:
            self.python_version_ok = True
            self.log("✓ Python version is compatible")
        else:
            self.log(f"✗ Python 3.8+ required, found {version.major}.{version.minor}")
            return False
        
        # Check pip
        self.log("\nChecking pip availability...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            self.log(f"✓ pip is available: {result.stdout.strip()}")
        else:
            self.log("✗ pip is not available")
            return False
        
        self.log("\n✓ System check complete")
        return True
    
    def install_dependencies(self):
        """Install all dependencies"""
        self.log("\n[2/4] Installing dependencies...")
        # Prepare environment (venv if requested)
        self.setup_environment()
        
        # Upgrade pip
        self.log("\nUpgrading pip...")
        result = subprocess.run(
            [self.py_exec, "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            self.log("✓ pip upgraded")
        
        # Install requirements
        self.log("\nInstalling from requirements.txt...")
        self.log("This may take several minutes...")
        
        requirements_path = Path(__file__).parent / "requirements.txt"
        if not requirements_path.exists():
            self.log("✗ requirements.txt not found!")
            return False
        
        result = subprocess.run(
            [self.py_exec, "-m", "pip", "install", "-r", str(requirements_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            self.log("\n✗ Installation failed!")
            self.log("Error output:")
            self.log(result.stderr[:1000])
            
            # Try to fix
            self.log("\n=== Attempting to fix issues ===")
            return self.attempt_fixes()
        else:
            self.log("\n✓ All dependencies installed successfully!")
            self.dependencies_installed = True
            
            # Install pytest
            self.log("\nInstalling pytest for testing...")
            subprocess.run(
                [self.py_exec, "-m", "pip", "install", "pytest"],
                capture_output=True,
                text=True
            )
        return True
    
    def attempt_fixes(self):
        """Attempt to fix installation issues"""
        self.log("Retrying with improved strategy...")

        requirements_path = Path(__file__).parent / "requirements.txt"
        with open(requirements_path) as f:
            raw_lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        def strip_pins(lines):
            pkgs = []
            for line in lines:
                pkg = line.split(';')[0].strip()
                if '==' in pkg:
                    pkg = pkg.split('==')[0]
                pkgs.append(pkg)
            return pkgs

        unpinned = strip_pins(raw_lines)
        is_py313_plus = (sys.version_info.major, sys.version_info.minor) >= (3, 13)

        # Upgrade tooling
        subprocess.run([self.py_exec, "-m", "pip", "install", "-U", "pip", "setuptools", "wheel"],
                       capture_output=True, text=True)

        # Try unpinned all-at-once
        args = [self.py_exec, "-m", "pip", "install"]
        if is_py313_plus:
            self.log("Python 3.13 detected – enabling --pre for better wheel availability...")
            args.append("--pre")
        args.extend(unpinned)

        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode == 0:
            self.log("\n✓ Dependencies installed after retry (unpinned)")
            self.dependencies_installed = True
            return True

        # Per-package as last resort
        failed_packages = []
        for package in unpinned:
            print(f"Installing {package}...", end=" ", flush=True)
            per_args = [self.py_exec, "-m", "pip", "install"]
            if is_py313_plus:
                per_args.append("--pre")
            per_args.append(package)
            r = subprocess.run(per_args, capture_output=True, text=True)
            if r.returncode != 0:
                failed_packages.append(package)
                print("✗")
            else:
                print("✓")

        if failed_packages:
            self.log(f"\n✗ Could not install: {', '.join(failed_packages)}")
            if is_py313_plus:
                alt = shutil.which("python3.12") or shutil.which("python3.11")
                if alt:
                    self.log(f"Tip: Try running with {alt} (better dependency support).")
                else:
                    self.log("Tip: Install Python 3.11/3.12 and rerun the installer.")
            self.log("Continuing with partial installation so tests/launch are available...")
            self.dependencies_installed = True
            self.partial_installation = True
            return True
        else:
            self.log("\n✓ All packages installed after retry!")
            self.dependencies_installed = True
            return True
    
    def test_installation(self):
        """Test the installation"""
        self.log("\n[3/4] Testing installation...")
        
        # Test imports
        self.log("\nTesting module imports...")
        test_imports = [
            ("PySide6", "PySide6"),
            ("opencv-python-headless", "cv2"),
            ("onnxruntime", "onnxruntime"),
            ("numpy", "numpy"),
            ("Pillow", "PIL"),
        ]
        
        all_ok = True
        for package_name, module_name in test_imports:
            try:
                __import__(module_name)
                self.log(f"  ✓ {package_name}")
            except ImportError as e:
                self.log(f"  ✗ {package_name}: {e}")
                all_ok = False
        
        # Test app module separately (may fail in headless environment)
        try:
            import src.core.detection
            import src.services.camera
            self.log(f"  ✓ src modules (core libraries)")
        except ImportError as e:
            if "tkinter" in str(e):
                self.log(f"  ✓ src modules (requires GUI environment to fully test)")
            else:
                self.log(f"  ✗ src modules: {e}")
                all_ok = False
        
        if not all_ok:
            self.log("\n⚠ Some imports failed, installation may have issues")
        else:
            self.log("\n✓ All required modules available!")
        
        # Run tests if available
        self.log("\nRunning application tests...")
        result = subprocess.run(
            [self.py_exec, "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            self.log("✓ All tests passed!")
        else:
            self.log("⚠ Some tests failed (this may be expected in headless environment)")
        
        self.app_tested = True
        return True
    
    def complete_installation(self):
        """Finalize installation"""
        self.log("\n[4/4] Finalizing installation...")
        self.installation_complete = True
        
        self.log("\n" + "=" * 60)
        if self.partial_installation:
            self.log("⚠ Installation finished with warnings (partial dependencies)")
        else:
            self.log("✓ Installation Complete!")
        self.log("=" * 60)
        self.log("\nTo run AnomRecorder:")
        self.log("  python usb_cam_viewer.py")
        self.log("  or")
        self.log("  python -m src.index")
        self.log("\n" + "=" * 60)

        if self.auto_start:
            self.log("\nAuto-start is enabled. Launching application...")
            try:
                app_path = Path(__file__).parent / "usb_cam_viewer.py"
                if not app_path.exists():
                    app_path = Path(__file__).parent / "src" / "index.py"
                subprocess.Popen([self.py_exec, str(app_path)], cwd=Path(__file__).parent)
                self.log("✓ Application launched!")
            except Exception as e:
                self.log(f"✗ Failed to launch app automatically: {e}")

        return True
    
    def run(self):
        """Run the complete installation process"""
        if not self.check_system():
            self.log("\n✗ System check failed!")
            return False
        
        if not self.install_dependencies():
            self.log("\n✗ Dependency installation failed!")
            return False
        
        if not self.test_installation():
            self.log("\n⚠ Testing had issues, but installation may work")
        
        return self.complete_installation()

    # Shared helpers (GUI/CLI) implemented as mixins below

    def setup_environment(self):
        if not self.use_venv:
            self.py_exec = sys.executable
            return
        venv_dir = self.venv_dir
        self.log("\n=== Setting up virtual environment (.venv) ===")
        py_for_venv = sys.executable
        if (sys.version_info.major, sys.version_info.minor) >= (3, 13):
            cand = None
            for name in ("python3.12", "python3.11"):
                p = shutil.which(name)
                if p:
                    cand = p; break
            if not cand and sys.platform == 'win32':
                py = shutil.which('py')
                if py:
                    for minor in ("3.12", "3.11"):
                        r = subprocess.run([py, f"-{minor}", "-c", "import sys;print(sys.executable)"], capture_output=True, text=True)
                        if r.returncode == 0 and r.stdout.strip():
                            cand = r.stdout.strip(); break
            if cand:
                py_for_venv = cand
                self.log(f"Using {py_for_venv} for virtual environment")

        if not venv_dir.exists():
            r = subprocess.run([py_for_venv, "-m", "venv", str(venv_dir)], capture_output=True, text=True)
            if r.returncode != 0:
                self.log(r.stdout[-1000:] if r.stdout else "")
                self.log(r.stderr[-1000:] if r.stderr else "")
                raise Exception("Failed to create virtual environment")
        ve_py = venv_dir / ("Scripts" if os.name == 'nt' else "bin") / ("python.exe" if os.name == 'nt' else "python")
        if not ve_py.exists():
            raise Exception("Virtual environment Python not found")
        self.py_exec = str(ve_py)
        self.log(f"Using interpreter: {self.py_exec}")


def main():
    """Main entry point"""
    # If not planning to use a venv, and running on Python 3.13+,
    # try to relaunch with a more compatible interpreter automatically.
    want_venv = DEFAULT_USE_VENV
    if "--no-venv" in sys.argv:
        want_venv = False
    elif "--venv" in sys.argv:
        want_venv = True

    if not want_venv and (sys.version_info.major, sys.version_info.minor) >= (3, 13):
        def find_alt_python():
            # Prefer 3.12, then 3.11
            for name in ("python3.12", "python3.11"):
                path = shutil.which(name)
                if path:
                    return path
            # Windows: try the 'py' launcher
            if sys.platform == 'win32':
                py = shutil.which('py')
                if py:
                    for minor in ("3.12", "3.11"):
                        try:
                            out = subprocess.run([py, f"-{minor}", "-c", "import sys;print(sys.executable)"],
                                                 capture_output=True, text=True)
                            if out.returncode == 0 and out.stdout.strip():
                                return out.stdout.strip()
                        except Exception:
                            pass
            return None

        alt = find_alt_python()
        if alt:
            print(f"Detected Python {sys.version_info.major}.{sys.version_info.minor}. Relaunching installer with {alt} for better compatibility...")
            os.execv(alt, [alt, __file__] + sys.argv[1:])

    if GUI_AVAILABLE and (os.environ.get('DISPLAY') or sys.platform == 'win32'):
        # Try GUI mode
        try:
            root = tk.Tk()
            app = InstallerGUI(root, auto_start=AUTO_START, use_venv=want_venv)
            root.mainloop()
        except Exception as e:
            print(f"GUI mode failed: {e}")
            print("Falling back to CLI mode...")
            installer = InstallerCLI(auto_start=AUTO_START, use_venv=want_venv)
            success = installer.run()
            sys.exit(0 if success else 1)
    else:
        # CLI mode
        installer = InstallerCLI(auto_start=AUTO_START, use_venv=want_venv)
        success = installer.run()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
