# Windows Installer Documentation

## Overview

AnomRecorder includes a **bulletproof Windows installer** designed for zero-friction installation on any Windows 10/11 machine. No manual steps, no terminal expertise required.

## Quick Start (TL;DR)

**Double-click:** `install.bat`

That's it. The installer handles everything automatically.

---

## Features

### ✅ 100% Automated
- No manual steps required
- No terminal knowledge needed
- No Python expertise required

### ✅ Bulletproof Error Handling
- Never crashes or shows raw stack traces
- Comprehensive error recovery
- Retry logic for transient failures
- Professional, user-friendly error messages

### ✅ Virtual Environment
- Automatically creates and uses `.venv`
- No pollution of global Python installation
- Reuses existing virtual environment if present

### ✅ Comprehensive Logging
- All operations logged to `installer.log`
- Detailed troubleshooting information
- Separate from application logs

### ✅ Auto-Launch
- Optionally launches application after installation
- Confirms successful startup
- Background process management

### ✅ Professional UX
- Clean, colorful terminal output
- Progress indicators
- Status messages at each step
- No scary red errors shown to users

---

## Installation Methods

### Method 1: PowerShell (Recommended)

The PowerShell installer provides the most robust experience with advanced error handling and retry logic.

**Run:**
```powershell
.\install.ps1
```

**Options:**
```powershell
# Silent installation (no prompts)
.\install.ps1 -Silent

# Don't launch application after install
.\install.ps1 -NoLaunch

# Skip virtual environment (use global Python)
.\install.ps1 -NoVenv

# Combine flags
.\install.ps1 -Silent -NoLaunch
```

### Method 2: Batch File (Universal)

The batch file wrapper automatically detects PowerShell and falls back to Python if needed.

**Run:**
```batch
install.bat
```

This is the **recommended method** for end users as it requires no knowledge of PowerShell or execution policies.

### Method 3: Python Script (Cross-Platform)

The Python installer provides a GUI (or CLI fallback) and works on all platforms.

**Run:**
```bash
python install.py
```

**Options:**
```bash
# Use virtual environment (recommended)
python install.py --venv

# Skip virtual environment
python install.py --no-venv

# Auto-start application after install
python install.py --start

# Combined
python install.py --venv --start
```

### Method 4: Legacy Batch (Deprecated)

For backwards compatibility:
```batch
install_dependencies.bat
```

This redirects to the new `install.bat`.

---

## Installation Steps (Automatic)

When you run the installer, it performs these steps automatically:

1. **System Requirements Check**
   - Verifies Python 3.8+ is installed
   - Checks pip availability
   - Validates venv module
   - Confirms requirements.txt exists

2. **Virtual Environment Setup**
   - Creates `.venv` directory (if not exists)
   - Reuses existing venv if present
   - Configures Python paths

3. **Dependency Installation**
   - Upgrades pip, setuptools, wheel
   - Installs all packages from requirements.txt
   - Retries on transient failures
   - Falls back to per-package installation if needed

4. **Installation Testing**
   - Tests critical module imports (PySide6, OpenCV, etc.)
   - Runs application tests if pytest available
   - Validates installation integrity

5. **Application Launch** (Optional)
   - Prompts to launch application
   - Starts in background process
   - Confirms successful startup

---

## Logging

### Installer Log

Location: `installer.log` (in project root)

Contains:
- Timestamp for each operation
- System information
- Detailed error messages
- Command outputs
- Installation status

**Use this file for troubleshooting installation issues.**

### Application Log

The application itself logs to console during normal operation. When built as an .exe with PyInstaller, logs are directed to system log facilities.

---

## Troubleshooting

### Python Not Found

**Error:** "Python is not installed or not in PATH"

**Solution:**
1. Download Python 3.8+ from https://www.python.org/downloads/
2. **Important:** Check "Add Python to PATH" during installation
3. Restart your terminal/command prompt
4. Run installer again

### Execution Policy Restricted (PowerShell)

**Error:** PowerShell script execution is disabled

**Solution:**
The installer automatically handles this. If you see this error when running PowerShell directly:

```powershell
# Temporary bypass (recommended)
powershell -ExecutionPolicy Bypass -File install.ps1

# Or permanently change policy (requires admin)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Better:** Just use `install.bat` which handles this automatically.

### Dependency Installation Failed

**Error:** Some packages could not be installed

**Possible Causes:**
- No internet connection
- Firewall blocking pip
- Incompatible package versions
- Python version too old/new

**Solutions:**
1. Check internet connection
2. Disable firewall/VPN temporarily
3. Try running as Administrator
4. Check `installer.log` for details
5. Try manual installation: `python -m pip install -r requirements.txt`

### Virtual Environment Creation Failed

**Error:** Could not create virtual environment

**Solution:**
1. Delete `.venv` folder if it exists (may be corrupt)
2. Run installer again
3. Or use `-NoVenv` flag to install globally:
   ```powershell
   .\install.ps1 -NoVenv
   ```

### Application Won't Launch

**Error:** Application fails to start after installation

**Solutions:**
1. Check `installer.log` for errors during testing phase
2. Try manual launch:
   ```batch
   .\.venv\Scripts\python.exe usb_cam_viewer.py
   ```
3. Verify USB camera is connected
4. Check System Requirements below

---

## System Requirements

### Minimum
- Windows 10 or Windows 11
- Python 3.8 or higher
- 4 GB RAM
- 2 GB free disk space
- USB camera (for camera features)

### Recommended
- Windows 11
- Python 3.10 or 3.11
- 8 GB RAM
- 10 GB free disk space (for recordings)
- USB 3.0 camera

### Network
- Internet connection required during installation (for downloading dependencies)
- No internet required for application usage (100% offline)

---

## Advanced Usage

### Silent Installation for Automation

For deployment scripts or automated setups:

```powershell
# PowerShell silent install
.\install.ps1 -Silent -NoLaunch

# Check exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host "Installation successful"
} else {
    Write-Host "Installation failed"
    Get-Content installer.log
}
```

```batch
REM Batch silent install
call install.bat
if %ERRORLEVEL% EQU 0 (
    echo Installation successful
) else (
    echo Installation failed
    type installer.log
)
```

### Custom Virtual Environment Location

Currently not supported. The installer always uses `.venv` in the project directory. This ensures consistency and simplifies path management.

### Upgrading / Reinstalling

To upgrade or reinstall:

1. Delete `.venv` folder (optional, for clean install)
2. Run `install.bat` again

The installer will:
- Reuse existing venv if present
- Upgrade packages to latest versions specified in requirements.txt
- Re-test installation

### Uninstallation

To remove AnomRecorder:

1. Delete the entire project directory
2. (Optional) Remove any recordings stored elsewhere

The installer does not modify your system Python installation or global packages (when using venv).

---

## Security Notes

### Execution Policy

The PowerShell installer uses `-ExecutionPolicy Bypass` for the installation session only. This does not permanently modify your system's execution policy.

### Administrator Rights

The installer does **not** require administrator rights. It installs everything in the user's local directory.

Some operations (like launching the application) may require standard user permissions for:
- Creating directories
- Accessing USB cameras
- Writing log files

### Network Security

The installer downloads packages from PyPI (Python Package Index) using pip. These are the official Python package repositories.

- All downloads use HTTPS
- Packages are verified by pip
- No third-party repositories are used

### Privacy

The installer:
- ✅ Does NOT send any data to external servers
- ✅ Does NOT collect telemetry
- ✅ Does NOT require account creation
- ✅ Logs everything locally only

---

## Files Created

The installer creates these files and directories:

```
project_root/
├── .venv/              # Virtual environment (if using --venv)
│   ├── Scripts/        # Python executable and tools
│   ├── Lib/            # Installed packages
│   └── ...
├── installer.log       # Installation log
├── recordings/         # Created at runtime by application
└── screenshots/        # Created at runtime by application
```

All files are contained within the project directory.

---

## For Developers

### Testing the Installer

Test on a clean Windows VM:

1. Clone repository
2. Ensure Python is NOT in PATH (to test error handling)
3. Run `install.bat`
4. Verify error message is user-friendly
5. Install Python
6. Run `install.bat` again
7. Verify successful installation

### Modifying the Installer

**PowerShell Script:** `install.ps1`
- Main installation logic
- Error handling functions
- Retry logic
- User interaction

**Batch Wrapper:** `install.bat`
- PowerShell detection
- Execution policy handling
- Python fallback
- Error message formatting

**Python Installer:** `install.py`
- GUI installer (Tkinter)
- CLI fallback
- Cross-platform support
- Dependency management

### Adding Dependencies

1. Add package to `requirements.txt`
2. Test installation on clean environment
3. Update README if package has special requirements

---

## Support

### Getting Help

1. Check `installer.log` for detailed error information
2. Review this documentation
3. Check main README.md for application usage
4. Open an issue on GitHub with:
   - Your `installer.log` file
   - Windows version
   - Python version
   - Error message or symptoms

### Known Issues

None currently reported. The installer has been designed to handle:
- ✅ Network interruptions
- ✅ Missing Python components
- ✅ Incompatible package versions
- ✅ Permission issues
- ✅ Corrupt virtual environments

---

## License

This installer is part of AnomRecorder and follows the same license terms as the main application.

---

**Made with ❤️ by AnomFIN**

*Ship intelligence, not excuses.*
