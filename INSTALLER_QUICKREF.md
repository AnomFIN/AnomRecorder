# AnomRecorder Windows Installer - Quick Reference

## For End Users

### Installation (One Command)

```batch
install.bat
```

**That's it!** Double-click the file or run from command prompt.

### What It Does

1. ✓ Checks your Python installation
2. ✓ Creates virtual environment (.venv)
3. ✓ Installs all dependencies automatically
4. ✓ Tests the installation
5. ✓ Launches the application (optional)

### Running the Application

After installation, use:

```batch
run.bat
```

Or:

```batch
.\.venv\Scripts\python.exe usb_cam_viewer.py
```

---

## For Developers

### Testing the Installer

Run the validation suite:

```bash
python test_installer_validation.py
```

### Manual Testing Checklist

On a clean Windows VM (or after deleting .venv):

- [ ] Run `install.bat` - should complete without errors
- [ ] Check `installer.log` - should contain detailed logs
- [ ] Verify `.venv` directory was created
- [ ] Verify all dependencies installed (check log)
- [ ] Try launching app with `run.bat`
- [ ] Confirm USB camera detection works

### Testing Error Scenarios

1. **Python not in PATH:**
   - Remove Python from PATH temporarily
   - Run `install.bat`
   - Should show friendly error message with download link

2. **Network failure:**
   - Disconnect from internet
   - Run `install.bat`
   - Should show appropriate error with suggestions

3. **Corrupted venv:**
   - Create a dummy `.venv` directory with invalid content
   - Run `install.bat`
   - Should detect and recreate venv

### PowerShell Options

```powershell
# Standard installation
.\install.ps1

# Silent mode (no prompts)
.\install.ps1 -Silent

# Don't launch after install
.\install.ps1 -NoLaunch

# Skip virtual environment
.\install.ps1 -NoVenv

# Combined
.\install.ps1 -Silent -NoLaunch
```

### Python Options

```bash
# Standard installation with GUI
python install.py

# Use virtual environment
python install.py --venv

# Skip virtual environment
python install.py --no-venv

# Auto-start after install
python install.py --start

# Combined
python install.py --venv --start
```

---

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| Python not found | Install Python 3.8+ from python.org, add to PATH |
| PowerShell restricted | Use `install.bat` instead (auto-handles this) |
| Dependencies fail | Check internet, try as Administrator, check `installer.log` |
| Venv creation fails | Delete `.venv` folder and try again, or use `-NoVenv` |
| App won't launch | Verify USB camera connected, check Python version |

---

## File Locations

| File | Purpose |
|------|---------|
| `install.bat` | Main installer launcher |
| `install.ps1` | PowerShell installer (advanced) |
| `install.py` | Python installer (cross-platform) |
| `run.bat` | Application launcher |
| `installer.log` | Installation log (for debugging) |
| `.venv/` | Virtual environment directory |
| `WINDOWS_INSTALLER.md` | Full documentation |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | System requirements not met |
| 1 | Dependency installation failed |
| 1 | Virtual environment creation failed |

---

## System Requirements

- Windows 10 or 11
- Python 3.8 or higher
- 4 GB RAM minimum
- 2 GB free disk space (more for recordings)
- Internet connection (for installation only)

---

## Support

1. Check `installer.log` for detailed error information
2. Review [WINDOWS_INSTALLER.md](WINDOWS_INSTALLER.md) for comprehensive guide
3. Review [README.md](README.md) for application documentation
4. Open GitHub issue with log file attached

---

**AnomFIN - Ship intelligence, not excuses.**
