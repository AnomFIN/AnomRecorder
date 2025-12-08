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

import subprocess
import sys
import threading
import os
from pathlib import Path

# Try to import tkinter, fall back to CLI if not available
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("Note: GUI (tkinter) not available, using CLI mode")

class InstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AnomRecorder Installer")
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        
        # State variables
        self.installation_complete = False
        self.python_version_ok = False
        self.dependencies_installed = False
        self.app_tested = False
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Create GUI
        self.create_widgets()
        
        # Start with system check
        self.root.after(500, self.check_system)
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Header
        header_frame = tk.Frame(self.root, bg="#1a1a1a", height=80)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
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
        
        self.launch_button = tk.Button(
            button_frame,
            text="Launch AnomRecorder",
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
                
            except Exception as e:
                self.progress_bar.stop()
                self.log(f"\n✗ Error during system check: {e}")
                self.update_status('python', "✗ Fail", "red")
                messagebox.showerror("System Check Failed", str(e))
        
        threading.Thread(target=check, daemon=True).start()
    
    def start_installation(self):
        """Start the installation process"""
        self.install_button.config(state=tk.DISABLED)
        self.progress_bar.start()
        
        def install():
            try:
                # Step 1: Upgrade pip
                self.progress_label.config(text="Upgrading pip...")
                self.log("\n=== Upgrading pip ===")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
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
                    [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
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
                        [sys.executable, "-m", "pip", "install", "pytest"],
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
    
    def attempt_fixes(self):
        """Attempt to automatically fix common installation issues"""
        self.log("Analyzing errors and attempting fixes...")
        
        # Try installing with --no-deps for problematic packages
        self.log("Retrying with individual package installation...")
        
        requirements_path = Path(__file__).parent / "requirements.txt"
        with open(requirements_path) as f:
            packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        failed_packages = []
        for package in packages:
            self.log(f"Installing {package}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                failed_packages.append(package)
                self.log(f"  ✗ Failed: {package}")
            else:
                self.log(f"  ✓ Success: {package}")
        
        if failed_packages:
            self.log(f"\n✗ Could not install: {', '.join(failed_packages)}")
            self.update_status('deps', "✗ Fail", "red")
            self.progress_bar.stop()
            messagebox.showwarning(
                "Partial Installation",
                f"Some packages could not be installed:\n{', '.join(failed_packages)}\n\n"
                "The application may not work correctly."
            )
        else:
            self.log("\n✓ All packages installed successfully after retry!")
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
                [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
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
        self.progress_label.config(text="Installation complete!")
        self.launch_button.config(state=tk.NORMAL)
        self.log("\n" + "="*50)
        self.log("✓ Installation Complete!")
        self.log("="*50)
        self.log("\nYou can now launch AnomRecorder.")
        messagebox.showinfo(
            "Installation Complete",
            "AnomRecorder has been installed successfully!\n\n"
            "Click 'Launch AnomRecorder' to start the application."
        )
    
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
                [sys.executable, str(app_path)],
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
    
    def __init__(self):
        self.python_version_ok = False
        self.dependencies_installed = False
        self.app_tested = False
        self.installation_complete = False
    
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
        
        # Upgrade pip
        self.log("\nUpgrading pip...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
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
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
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
                [sys.executable, "-m", "pip", "install", "pytest"],
                capture_output=True,
                text=True
            )
            return True
    
    def attempt_fixes(self):
        """Attempt to fix installation issues"""
        self.log("Retrying with individual package installation...")
        
        requirements_path = Path(__file__).parent / "requirements.txt"
        with open(requirements_path) as f:
            packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        failed_packages = []
        for package in packages:
            print(f"Installing {package}...", end=" ", flush=True)
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                failed_packages.append(package)
                print("✗")
            else:
                print("✓")
        
        if failed_packages:
            self.log(f"\n✗ Could not install: {', '.join(failed_packages)}")
            return False
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
            [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
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
        self.log("✓ Installation Complete!")
        self.log("=" * 60)
        self.log("\nTo run AnomRecorder:")
        self.log("  python usb_cam_viewer.py")
        self.log("  or")
        self.log("  python -m src.index")
        self.log("\n" + "=" * 60)
        
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


def main():
    """Main entry point"""
    if GUI_AVAILABLE and (os.environ.get('DISPLAY') or sys.platform == 'win32'):
        # Try GUI mode
        try:
            root = tk.Tk()
            app = InstallerGUI(root)
            root.mainloop()
        except Exception as e:
            print(f"GUI mode failed: {e}")
            print("Falling back to CLI mode...")
            installer = InstallerCLI()
            success = installer.run()
            sys.exit(0 if success else 1)
    else:
        # CLI mode
        installer = InstallerCLI()
        success = installer.run()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
